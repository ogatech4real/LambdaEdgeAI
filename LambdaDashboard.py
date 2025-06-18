import streamlit as st
import boto3
from datetime import datetime, timezone, timedelta
import pandas as pd
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from decimal import Decimal
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import requests

# --- Streamlit Setup ---
st.set_page_config(
    page_title="LambdaEdge - Fault Event Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
st_autorefresh(interval=60 * 1000, key="datarefresh")  # Refresh every 60 seconds
st.title("📊 LambdaEdge - Fault Event Dashboard")
st.markdown("This App Manages Equipment Health in Real-Time and Use to Visualise Process Variables Loaded from DynamoDB logs.")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Select Range")
time_window = st.sidebar.slider("Time window (minutes)", 5, 240, 60)

# --- Initialize DynamoDB ---
try:
    session = boto3.Session(
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
        region_name=st.secrets["aws"]["region"]
    )
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('FaultEventLog')
except (NoCredentialsError, PartialCredentialsError, KeyError):
    st.error("❌ AWS credentials not found in Streamlit secrets.")
    st.stop()

# --- Helper: Safe conversion ---
def safe_cast(val):
    if isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, str) and val.isdigit():
        return int(val)
    return val

# --- Data Extraction ---
def fetch_fault_data():
    try:
        response = table.scan()
        items = response.get('Items', [])
        records = []
        for item in items:
            payload = item.get("payload", {})
            try:
                records.append({
                    "device_id": payload.get("device_id") or item.get("device_id"),
                    "timestamp": int(safe_cast(payload.get("timestamp") or item.get("timestamp"))),
                    "temperature": float(safe_cast(payload.get("temperature") or item.get("temperature"))),
                    "vibration": float(safe_cast(payload.get("vibration") or item.get("vibration"))),
                    "status": payload.get("status") or item.get("status", "UNKNOWN")
                })
            except:
                continue
        return records
    except Exception as e:
        st.error(f"❌ Data fetch failed: {e}")
        return []

# --- Load + Filter ---
data = fetch_fault_data()
if not data:
    st.warning("⚠️ No data available.")
    st.stop()

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window)
df = df[df['timestamp'] >= cutoff_time]

# --- Device Selection ---
unique_devices = df['device_id'].unique().tolist()
selected_device = st.sidebar.selectbox("📟 Select Device to View", unique_devices)
chart_selection = st.sidebar.radio("📉 Select Chart to View", ["Temperature", "Vibration", "Fault Trend"])

filtered_df = df[df['device_id'] == selected_device]
if filtered_df.empty:
    st.info(f"No data for device {selected_device}.")
    st.stop()

latest = filtered_df.sort_values(by='timestamp', ascending=False).iloc[0]

# --- Summary Status Metrics ---
st.subheader(f"📈 Summary Status Metrics [{selected_device}]")
# Expected and actual record count
expected_count = time_window  # assuming 1 record per minute
actual_count = len(filtered_df)
# Compute status counts only for OK, WARNING, and FAULT (ignore OFFLINE, UNKNOWN etc.)
status_focus = ["OK", "WARNING", "FAULT"]
status_counts = {status: filtered_df[filtered_df["status"] == status].shape[0] for status in status_focus}
# Display metrics
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
c1.metric("✅ OK", status_counts.get("OK", 0))
c2.metric("⚠️ WARNING", status_counts.get("WARNING", 0))
c3.metric("🚨 FAULT", status_counts.get("FAULT", 0))
# Completeness check with percentage
completion_rate = round((actual_count / expected_count) * 100, 1)
completion_status = f"{actual_count}/{expected_count} ({completion_rate}%)"
c4.metric("📦 Data Completeness", completion_status)

# caption to show timestamp range and alert if data is missing
col1, col2 = st.columns([3, 2])  # You can adjust width ratio as needed
with col1:
    st.caption(f"ℹ️ Received {actual_count} out of {expected_count} expected entries for `{selected_device}`.")
with col2:
    st.warning("⚠️ If <100%, Some telemetry records may be delayed.")

# === SECTION 2: Live Telemetry Data Table ===
st.subheader(f"📋 Live Telemetry Data [{selected_device}]")
# Define the sorted DataFrame explicitly
sorted_df = filtered_df.sort_values(by='timestamp', ascending=False)[['timestamp', 'temperature', 'vibration', 'status']]
# Show the table
st.dataframe(sorted_df, use_container_width=True)
# Generate CSV data
csv_data = sorted_df.to_csv(index=False).encode('utf-8')
# Add download button
st.download_button(
    label="📥 Download CSV",
    data=csv_data,
    file_name=f"{selected_device}_telemetry.csv",
    mime="text/csv"
)

# === SECTION 3: Device Health Snapshot ===
st.subheader(f"📟 Device Health Snapshot [{selected_device}]")
st.markdown(
    f"**Device:** `{selected_device}` | "
    f"**Status:** `{latest['status']}` | "
    f"**Last Seen (UTC):** `{latest['timestamp']}`"
)

# === SECTION 4: Telemetry Gauges ===
st.subheader(f"📟 Live Telemetry Gauges [{selected_device}]")
g1, g2 = st.columns(2)

fig_temp = go.Figure(go.Indicator(
    mode="gauge+number",
    value=latest['temperature'],
    title={'text': "Temperature (°C)"},
    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#FF5733"}}
))
fig_vib = go.Figure(go.Indicator(
    mode="gauge+number",
    value=latest['vibration'],
    title={'text': "Vibration (mm/s)"},
    gauge={'axis': {'range': [0, 0.2]}, 'bar': {'color': "#33C3FF"}}
))
g1.plotly_chart(fig_temp, use_container_width=True)
g2.plotly_chart(fig_vib, use_container_width=True)

# === SECTION 5: Chart Over Time ===
st.subheader(f"📉 {chart_selection} Over Time [{selected_device}]")
if chart_selection == "Fault Trend":
    df_faults = filtered_df[filtered_df['status'] == 'FAULT']
    if not df_faults.empty:
        df_faults['bucket'] = df_faults['timestamp'].dt.floor('15min')
        chart_data = df_faults.groupby('bucket').size().reset_index(name='Fault Count')
        st.line_chart(chart_data.set_index('bucket'))
    else:
        st.info("No FAULT events to display.")
else:
    time_series = filtered_df.set_index('timestamp').sort_index()
    st.line_chart(time_series[[chart_selection.lower()]])

# === Lambda Predictive Inference Handler ===
st.subheader("🤖 Predictive Diagnostics")
st.info("This section displays ML-inferred anomaly risks and failure probabilities.")
def get_prediction(device_id, temp, vib):
    try:
        endpoint = "https://oh7n7tfwa2kiy2gpxgpjcdrz6q0cpdox.lambda-url.eu-north-1.on.aws/"
        payload = {
            "device_id": device_id,
            "temperature": temp,
            "vibration": vib
        }
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()

        result = response.json()
        if "prediction" in result:
            return result
        else:
            return {"error": "Missing 'prediction' key in Lambda response", "raw": result}

    except requests.exceptions.RequestException as e:
        return {"error": f"HTTP error: {e}"}

    except ValueError as e:
        return {"error": f"JSON decoding failed: {e}"}

# === Predictive Inference UI Handler ===
with st.expander("🔍 Run Predictive Inference"):
    selected_device = st.selectbox("Select Device", df["device_id"].unique())
    selected_data = df[df["device_id"] == selected_device].iloc[-1]

    if st.button("🚀 Run Inference"):
        result = get_prediction(
            device_id=selected_device,
            temp=selected_data["temperature"],
            vib=selected_data["vibration"]
        )

        if "error" in result:
            st.error(result["error"])
            if "raw" in result:
                st.json(result["raw"])
        else:
            # Display Metrics
            st.metric("Risk Score", result["risk_score"])
            st.metric("Confidence", result["confidence"])
            st.metric("Failure Mode", result["failure_mode"])

            # Color-coded result display
            color = "red" if result["prediction"] == "High Risk" else "green"
            st.markdown(
                f"<div style='background-color:{color};padding:15px;border-radius:10px;color:white;font-weight:bold;text-align:center;'>"
                f"Prediction: {result['prediction']}<br>Risk Score: {result['risk_score']}"
                f"</div>",
                unsafe_allow_html=True
            )

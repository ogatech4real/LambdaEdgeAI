# LambdaEdge – Predictive Fault Diagnostics Dashboard

![Project Badge](https://img.shields.io/badge/built%20with-AWS%20Lambda-blue) ![Streamlit](https://img.shields.io/badge/ui-Streamlit-orange) ![status](https://img.shields.io/badge/status-active-brightgreen)

## Overview

**LambdaEdge** is a real-time, serverless **predictive fault monitoring system** for industrial assets. It ingests telemetry data (temperature, vibration) from edge devices, logs it to AWS DynamoDB, and visualizes the data through a live Streamlit dashboard.

The system also integrates a **predictive AI engine** via AWS Lambda to detect anomaly risks and estimate failure probabilities, enabling proactive maintenance decisions.

At the core of the solution is a Lambda function that simulates telemetry data from three virtual industrial devices. These devices represent real-world machines, and the simulated data includes critical process variables such as temperature, vibration, and operational status. The Lambda function is triggered automatically every minute using Amazon EventBridge, ensuring continuous data generation. While this simulation provides a development-friendly way to model the system, it also mirrors how real telemetry could be ingested using AWS IoT Core. In a production scenario, physical devices can publish sensor data via MQTT over edge gateways, and AWS IoT Core would route this data into the same backend pipeline. This demonstrates how easily this solution can scale from simulation to real-world deployments.

All telemetry data is persistently stored in a DynamoDB table. From there, it becomes the basis for diagnostics and visualization. Threshold logic built into the Lambda simulator reflects real-world maintenance practices. For temperatures exceeding 80°C and vibration levels above 2.5 mm/s are red flags for conditions like bearing failure or early misalignment, which is triggered. These values aren’t random; they reflect the kinds of metrics engineers closely monitor in predictive maintenance programs.

---

## Features

-  **Serverless Design** (Lambda + DynamoDB + Streamlit)
-  **Auto-Refreshing Dashboard** (every 60 seconds)
-  **Live Gauges & Charts** for each device
-  **Real-Time Fault Detection** via status classification
-  **ML Inference** using AWS Lambda Function URL
-  **Historical Trends** (Temperature, Vibration, Faults)
-  **CSV Download** for telemetry records

---

## System Components & Workflow

| Component        | Role                                                                 |
|------------------|----------------------------------------------------------------------|
| **Lambda Injector** | Simulates telemetry (temperature, vibration, status) for 3 virtual devices. |
| **EventBridge**      | Triggers the Lambda Injector every minute (or user-defined rate).       |
| **DynamoDB**         | Persistent store for all injected telemetry data (`FaultEventLog`).     |
| **Streamlit App**    | Live dashboard deployed on **Streamlit Community Cloud** — always available to end users. |
| **IAM Roles**        | Enforces secure execution of Lambda functions and resource access using fine-grained AWS permissions. |

---

## Automated Simulation & Logging Flow

```text
[EventBridge Schedule]
         ↓ (every 1 min)
[Lambda Injector]
         ↓
[Simulated Telemetry (3 devices)]
         ↓
[AWS DynamoDB → FaultEventLog table]
         ↓
[Streamlit Dashboard ↔ Lambda Inference API (on-demand)]

## 🛠️ Tech Stack

| Component         | Tech/Service              |
|------------------|---------------------------|
| Serverless Logic | AWS Lambda (Function URL) |
| Scheduling       | Amazon EventBridge        |
| Storage          | AWS DynamoDB              |
| Frontend         | Streamlit (Python)        |
| Visualization    | Plotly + Streamlit Charts |
| ML Inference     | Hosted in Lambda (Python) |
| Integration      | boto3, requests, pandas   |

---

## Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/lambdaedge-dashboard.git
cd lambdaedge-dashboard
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

Make sure your environment is configured with access to `eu-north-1` and has permission to access the `FaultEventLog` DynamoDB table.

```bash
aws configure
```

### 4. Run the Dashboard

```bash
streamlit run app.py
```

---

## How AWS Lambda Was Used

### Lambda Injector

- Triggered by EventBridge every minute  
- Simulates telemetry from 3 virtual devices  
- Writes results to DynamoDB  

### ML Inference Lambda

- Deployed via Function URL  
- Accepts telemetry (`temperature`, `vibration`) via HTTP POST  
- Returns:
  - Risk classification (e.g., `High Risk`, `Low Risk`)
  - Risk score
  - Confidence level
  - Probable failure mode

---

## UI Output – Metrics & Visuals

| Metric        | Widget Type       | Description                            |
|---------------|-------------------|----------------------------------------|
| Prediction    | Colored HTML card | Displays "High Risk", "Low Risk", etc. |
| Risk Score    | `st.metric()`     | Value between 0–100                    |
| Confidence    | `st.metric()`     | Probability (0.0–1.0)                  |
| Failure Mode  | `st.metric()`     | Textual fault diagnosis                |
| Status Card   | Styled Markdown   | Red or green background                |

---

## Result Variants (Examples)

| Conditions                  | Prediction    | Risk Score | Confidence | Failure Mode       |
|-----------------------------|---------------|------------|------------|--------------------|
| Temp: 80+, Vib: 2.5+        | High Risk     | 91.2       | 0.94       | Bearing Failure    |
| Temp: 70–79, Vib: 1.5–2.4   | Medium Risk*  | 67.0       | 0.81       | Early Misalignment |
| Temp: <70, Vib <1.0         | Low Risk      | 23.4       | 0.98       | None Detected      |
| Lambda unreachable          | —             | —          | —          | “HTTP error…”      |
| Lambda returns HTML error   | —             | —          | —          | “JSON decoding…”   |

> *Note: Future versions may support additional prediction tiers such as **Medium Risk** and multiple **failure modes**. The dashboard logic is designed to accommodate these enhancements.*

---

## 🚀 Planned Enhancements

| Feature                   | Benefit                                         |
|---------------------------|--------------------------------------------------|
| `streamlit-echarts` gauge | Visualize `risk_score` in a dynamic gauge       |
| Cache inference responses | Reduce redundant Lambda calls                   |
| Model selection dropdown  | Support multiple ML models per device           |
| Risk trend graph          | Time-series view of risk levels per device      |

---

## Demo Video

 **Watch Demo Video**  
*(3 minutes – shows data flow, dashboard, and predictive insight in action)*

---

## AWS Services Used

- ✅ **AWS Lambda** (telemetry injector + predictive inference)  
- ✅ **Amazon EventBridge** (scheduler for injector Lambda)  
- ✅ **AWS DynamoDB** (fault logs)  
- ✅ **Amazon CloudWatch** (optional for logs)  
- ✅ **IAM Roles** (Lambda + DB access)  
- ⚙️ **AWS IoT Core** *(optional extension for edge ingestion)*  
- ⚠️ **Amazon SNS** *(optional for alerts/notifications)*  

---

## Sample Output

> *(Add a screenshot of your dashboard here if needed)*

---

## 👤 Author

**Adewale**  
[LinkedIn Profile](https://www.linkedin.com/in/your-profile)  
Built for the **[AWS Lambda Hackathon 2025](https://devpost.com/hackathons)**

---

## 🏁 Submission Info

- 🔗 Public Code: [GitHub Repo](https://github.com/yourusername/lambdaedge-dashboard)  
- 📹 Video Demo: [YouTube](https://youtube.com/link-to-your-video)  
- 🛠 AWS Used: Lambda, EventBridge, DynamoDB, Streamlit  
- 🗓 Submitted: June 2025  

---

## 📄 License

**MIT License**

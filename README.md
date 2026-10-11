# FloodRescue AI

> **Tagline:** Every Distress Signal Matters. Every Rescue Counts.  
> **Hackathon:** WeMakeDevs × AWS Environmental Hackathon 2026  
> **Track:** Heat and Water — Flood-Related Disaster Response  
> **Category:** Agents and AI  

---

## 1. The Environmental Problem

Climate change and severe meteorological anomalies have dramatically amplified the frequency and severity of flash flooding, monsoons, and extreme urban inundations. In inundated cities and rural floodplains:
- Thousands of citizens become rapidly marooned on rooftops, higher floors, and isolated structures as water levels surge beyond 4–6 feet in minutes.
- Emergency 911/112 dispatch centers are instantaneously paralyzed by thousands of disconnected phone calls, SMS distress signals, and social media pleas.
- Response coordinators lack a unified situational picture of where victims are trapped, who has life-threatening medical conditions (e.g. oxygen depletion, trauma, infants, elderly), and where specialized assets (swift-water boats vs. high-axle trucks) must be deployed.

---

## 2. Target Users

1. **Flood Survivors & Trapped Citizens:** Individuals stranded in rising floodwaters who need to transmit a structured SOS in seconds without registering an account or remembering passwords.
2. **Multi-Agency Incident Commanders & 911 Responders:** Emergency operations coordinators who need a clear, prioritized geospatial dashboard to verify reports, review AI triage insights, and authorize rescue sorties.
3. **Field Rescue Teams (NDRF, SDRF, Volunteers):** Swift-water boat squads, paramedics, and truck operators who receive direct dispatch orders and synchronize mission status in real time.

---

## 3. The Proposed Solution

**FloodRescue AI** is an AI-assisted flood distress reporting and rescue coordination platform. It acts as an intelligent, transparent information intermediary between citizens in crisis and authorized rescue personnel:
- Allows survivors to send a distress signal with exact GPS or approximate landmark descriptions, trapped headcounts, water depths, and acute medical emergencies.
- Leverages the **AWS Strands Agents SDK** and deterministic safety rules to extract structured intelligence from natural-language messages, check for duplicate clusters, and recommend priority without replacing human incident commanders.
- Provides an operational command map and dispatch queue with live status updates reflected back to survivors in real time.

---

## 4. Main Features

- 🚨 **Frictionless Mobile SOS (`/help`):** Report distress in seconds without login barrier. Accepts GPS or landmark addresses with visual precision indicators (`exact` vs `approximate`).
- 🤖 **AWS Strands AI Agent Triage:** Analyzes unstructured messages using strictly controlled tools, detects acute life threats, checks nearby incident clusters, and explains the reasoning behind each recommendation.
- 🛡️ **Deterministic Safety-First Layer:** Life-threatening emergencies (submerged roofs, chest-deep water, unconscious victims) automatically trigger `CRITICAL` priority before AI inference begins.
- 🗺️ **Geospatial Command Map (`/responder`):** Real-time Leaflet map with color-coded priority pins, cluster analysis, and strict distinction between **People Reported** and **Known Incidents**.
- 🚚 **Field Fleet Management (`/teams`):** Tracks availability, capabilities (swift-water boats, paramedics, 4x4 trucks), and assigned sorties.
- 💬 **Two-Way Dispatch Channel:** Responders and survivors can exchange mission updates directly on the incident thread.
- 🔄 **Idempotency Protection:** Prevents duplicate incident creation during repeated clicks on weak mobile connections.
- 🌐 **Graceful Cloud Fallback:** Seamlessly operates offline or in local simulation mode (`APP_MODE=local`) if cloud model credentials are unavailable.

---

## 5. System Architecture

```
[Survivor (Mobile/Web)]
       │
       ▼ (POST /incidents)
[Amazon API Gateway / Local FastAPI Adapter]
       │
       ▼
[AWS Lambda Service Layer (Validation & Idempotency)]
       │
       ├──► [Amazon DynamoDB / Local JSON Persistence] (Saved First!)
       │
       ▼
[AWS Strands AI Agent Engine (Amazon Bedrock / Fallback Triage)]
       ├── Tool: get_incident_details
       ├── Tool: search_nearby_incidents
       ├── Tool: get_available_rescue_teams
       ├── Tool: get_team_details
       ├── Tool: summarize_incident & recommend_priority
       └── Tool: draft_survivor_update
       │
       ▼ (Deterministic Safety Rules + Enriched AI Recommendation)
[Rescue Operations Dashboard (/responder)]
       │ (Human Verification & Team Assignment: POST /incidents/{id}/assign)
       ▼
[Assigned Rescue Team (/teams)] ──► [Incident Status Update] ──► [Survivor Tracking (/help?id=...)]
```

---

## 6. AWS Services Actually Used

1. **Amazon Bedrock:** Foundational model inference (Anthropic Claude 3 Haiku / Amazon Nova) invoked via the AWS Strands Agents SDK.
2. **AWS Lambda:** Serverless execution for API routing, validation guards, and AI agent orchestration.
3. **Amazon API Gateway:** HTTP API providing secure, low-latency endpoints and CORS integration.
4. **Amazon DynamoDB:** Serverless NoSQL persistence for incidents, teams, messages, and audit trails with Pay-Per-Request billing and Global Secondary Indexes.
5. **AWS SAM (Serverless Application Model):** Infrastructure-as-Code template (`infrastructure/template.yaml`) defining least-privilege IAM roles and serverless architecture.
6. **AWS Amplify Hosting / S3 + CloudFront:** Static web hosting for the React TypeScript application.

---

## 7. AI Agent Explanation (AWS Strands Agents SDK)

The AI agent is built using the **AWS Strands Agents SDK** (`strands-agents`) and runs under strict safety guardrails:
- **Sandbox Tool Calling:** The agent does not have arbitrary database write permissions or shell access. It interacts exclusively through 7 typed, validated tools:
  - `get_incident_details(incident_id)`
  - `search_nearby_incidents(latitude, longitude, radius_km)`
  - `get_available_rescue_teams()`
  - `get_team_details(team_id)`
  - `summarize_incident(incident_id)`
  - `recommend_priority(incident_id)`
  - `draft_survivor_update(incident_id, status)`
- **Explainability:** The agent articulates *why* a priority is flagged (e.g. *"Chest-deep water reported with elderly asthma patient"*), rather than emitting an opaque numerical score.
- **Fail-Safe Fallback:** If Bedrock credentials are not detected or throttled, the agent gracefully falls back to deterministic safety triage rules without dropping the report.

---

## 8. Local Setup & Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ (tested on Node 24)

### 1. Backend Setup
```bash
# In project root:
# 1. Activate Python virtual environment:
.\venv\Scripts\Activate.ps1    # On Windows
# source venv/bin/activate     # On Linux/macOS

# 2. Run backend API:
python -m uvicorn backend.api.app:app --reload --port 8000
```
Backend runs at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
# In a new terminal:
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

### 3. Seed Demo Data
Click the **Seed Demo Data** button in the top navigation bar or invoke:
```bash
curl -X POST http://localhost:8000/seed-simulated-data
```

---

## 9. AWS Deployment Instructions

For complete cloud deployment instructions using AWS SAM and AWS Amplify, consult [`DEPLOYMENT.md`](./DEPLOYMENT.md):
```bash
cd infrastructure
sam build
sam deploy --guided
```

---

## 10. Automated Testing

Run the automated test suite covering all 13 core acceptance scenarios:
```bash
.\venv\Scripts\python.exe -m pytest -v tests/test_backend.py
```
**Test Status:** 13/13 Passed (100% pass rate in 0.83s). See [`TESTING.md`](./TESTING.md) for full report.

---

## 11. Security, Privacy & Compliance

- **No Public PII Exposure:** Survivors can only access their specific incident tracking thread using their private incident ID.
- **Idempotency Protection:** Duplicate requests with the same idempotency key return the original incident without spawning duplicate records.
- **Immutable Audit Logging:** Every administrative action (acknowledgment, assignment, resolution) writes to an audit ledger.
- **No Hardcoded Secrets:** Configured using environment variables via `.env.example`.

---

## 12. Known Limitations & Disaster Context Boundaries

1. **Cellular Network Discovery:** Web applications cannot enumerate all mobile subscribers connected to nearby cell towers without carrier gateway partnerships. FloodRescue AI strictly counts reported individuals from verified citizen submissions.
2. **Hydrological Routing:** Water currents, submerged road hazards, and fallen power lines require human incident commander verification before dispatch.
3. **Human In The Loop:** The AI agent acts solely as an advisory assistant; only authorized human commanders can authorize dispatches or mark incidents resolved.

---

## 13. Three-Minute Demo Video

- **Video Link:** *[Insert YouTube demo link here]*
- **Demo Script:** Full timed storyboard available in [`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md).

---

## 14. Credits & Acknowledgements

- **AWS Strands Agents SDK:** Open-source model-driven SDK for Python AI agents.
- **Leaflet & OpenStreetMap:** Open geospatial mapping infrastructure.
- **WeMakeDevs & Amazon Web Services:** Host and sponsor of the WeMakeDevs × AWS Environmental Hackathon 2026.

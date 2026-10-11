# FloodRescue AI — Implementation Plan
**WeMakeDevs × AWS Environmental Hackathon 2026**
*Track: Heat and Water (Flood Response) | Category: Agents and AI*
*Tagline: Every Distress Signal Matters. Every Rescue Counts.*

---

## 1. Executive Summary & Architecture Overview

FloodRescue AI is an end-to-end, AI-assisted flood distress reporting and rescue coordination platform. In catastrophic flood scenarios, emergency dispatch centers are overwhelmed with disjointed calls, SMS messages, and social media pleas. FloodRescue AI bridges the gap between affected citizens (survivors) and authorized response units:

1. **Survivors** report distress via a lightweight, accessible web application (with GPS or landmark fallback, people count, medical emergencies, rising water danger).
2. **Backend & Persistence** immediately stores and confirms reports via AWS Lambda & DynamoDB (with a zero-dependency local JSON/SQLite persistence adapter for offline local mode).
3. **AWS Strands Agents SDK** powers a specialized disaster response triage agent that analyzes unstructured messages, extracts key attributes, identifies urgent medical/life-threatening flags, searches nearby incidents for deduplication, and recommends priority without replacing human command.
4. **Responders & Rescue Teams** view a real-time operational map and dispatch queue, acknowledge incidents, verify locations, assign teams, and post status updates that survivors can track in real time.

### End-to-End Flow Diagram
```
[Survivor (Mobile/Web)]
       │
       ▼ (POST /incidents)
[Amazon API Gateway / Local FastAPI Adapter]
       │
       ▼
[AWS Lambda Service Layer (Validation & Idempotency)]
       │
       ├──► [Amazon DynamoDB / Local JSON Persistence] (Incident Saved First)
       │
       ▼
[AWS Strands AI Agent Engine (Amazon Bedrock / Fallback Triage)]
       ├── Tool: get_incident_details
       ├── Tool: search_nearby_incidents
       ├── Tool: get_available_rescue_teams
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

## 2. Operating Modes

To guarantee continuous functionality without hidden failures, the application strictly supports two explicit modes:

1. **Local Development Mode (`APP_MODE=local`)**:
   - Zero external cloud requirement.
   - Uses local persistence adapter (`data/local_db.json`).
   - Uses rule-based deterministic AI triage parser and mock Strands Agent runner if AWS Bedrock credentials are not present.
   - Clearly labels all demonstration data as `[SIMULATED]`.
   - Never mocks API successes silently.

2. **AWS Cloud Mode (`APP_MODE=aws`)**:
   - Direct integration with deployed AWS API Gateway, AWS Lambda, Amazon DynamoDB.
   - Amazon Bedrock model invocation via AWS Strands Agents SDK (`strands-agents`).
   - Explicitly reports any missing IAM permissions, throttling, or Bedrock quota errors with graceful fallback to deterministic priority triage.

---

## 3. Ordered Development Phases

### Phase 1: Environment & Plan (Current)
- Inspect environment tools: Node 24, npm 11, Python 3.11, Git verified.
- Detect missing AWS CLI / SAM CLI (documented as deployment environment constraint).
- Set up Python virtual environment (`venv`) with `strands-agents`, `fastapi`, `uvicorn`, `pydantic`, `boto3`, `pytest`.
- Initialize repository structure and create `IMPLEMENTATION_PLAN.md`.

### Phase 2: Basic Working Application (Frontend & Local API)
- Scaffold Vite + React + TypeScript + Tailwind CSS application.
- Build Survivor SOS interface (`/help`):
  - Emergency SOS banner, people count validation, GPS permission & manual Leaflet pin placement, landmark input, medical urgency flags, water level indicators, special needs toggles, distress message.
  - Idempotency key generation, submission confirmation, unique incident ID, persistent incident tracking view.
- Build Local Persistence and API Adapter:
  - Models for Incidents, Teams, Messages, AuditEvents.
  - CRUD operations and pagination.
- Test end-to-end survivor reporting workflow.

### Phase 3: AWS Backend Architecture & Lambda Handlers
- Implement AWS Lambda handler patterns for API Gateway HTTP APIs:
  - `POST /incidents`, `GET /incidents`, `GET /incidents/{id}`, `PATCH /incidents/{id}`
  - `POST /incidents/{id}/messages`, `GET /incidents/{id}/messages`
  - `GET /teams`, `GET /teams/{id}`
  - `POST /incidents/{id}/assign`, `POST /incidents/{id}/acknowledge`, `POST /incidents/{id}/resolve`
  - `POST /incidents/{id}/analyze`
  - `GET /health`
- DynamoDB table schema design (single-table or dedicated tables with GSI for status and timestamp).
- AWS SAM template (`template.yaml`) defining Serverless functions, HttpApi, DynamoDB tables, IAM least-privilege roles.
- Run backend unit tests verifying handlers and persistence.

### Phase 4: AWS Strands AI Agent Implementation
- Integrate `strands-agents` SDK with Python Bedrock provider.
- Implement strictly controlled agent tools:
  - `get_incident_details(incident_id)`
  - `search_nearby_incidents(latitude, longitude, radius_km)`
  - `get_available_rescue_teams()`
  - `get_team_details(team_id)`
  - `summarize_incident(incident_id)`
  - `recommend_priority(incident_id)`
  - `draft_survivor_update(incident_id, status)`
- Implement deterministic safety priority rules (immediate threat to life, medical emergency, trapped children/elderly, rising water level).
- AI failure handling: Timeout wrappers, bounded retries, deterministic fallback flag `ai_processing_status: "fallback_rules_only"`.
- Unit tests for AI parsing, tool schemas, missing data identification, and fallback resilience.

### Phase 5: Rescue Operations & Team Dispatch Interfaces
- Build Responder Dashboard (`/responder`):
  - Operations metrics: Total People Reported, Known Reported Incidents, Urgent Review Queue, Location Verification Queue, Assigned, Resolved.
  - Interactive Leaflet map with colored priority markers, clustered views, and coordinate validity checks.
  - Multi-attribute filter & search (status, urgency, time, radius).
  - Incident detail drawer with AI analysis breakdown, explainability reasons, survivor messages, and assignment controls.
- Build Rescue Team Interface (`/teams`):
  - Team status card, assigned incident references, acknowledge assignment button, mark arrived / rescue completed.
  - Two-way communication channel between responder and survivor incident thread.
- Role-based authorization guard (role simulation for demo: `survivor`, `responder`, `team`).

### Phase 6: Reliability, Security & Testing Suite
- Comprehensive automated test suite covering all 32 mandatory test scenarios:
  - Unit tests for Pydantic models, validation, idempotency.
  - Integration tests for API endpoints and status transition guards.
  - Strands agent mock and live tests.
  - End-to-end simulated workflow test.
- Security hardening: Input sanitization, CORS configuration, no secrets in client or repo, structured audit logging.

### Phase 7: AWS Deployment Preparation & Instructions
- Complete `template.yaml` and `DEPLOYMENT.md` with SAM build/deploy instructions.
- Provide step-by-step setup for AWS Amplify Hosting / S3 + CloudFront frontend.
- Document exact required IAM policies, Bedrock model access prerequisites, and cost estimation.
- Provide verification commands using `curl` / PowerShell.

### Phase 8: Hackathon Deliverables & Polish
- Write comprehensive `README.md` with architecture diagrams, setup, screenshots, and credits.
- Prepare `DEMO_SCRIPT.md` (3-minute timed scenario script).
- Create `SUBMISSION_CHECKLIST.md`, `ARCHITECTURE.md`, `API.md`, `TESTING.md`, `.env.example`.
- Seed realistic simulated flood scenarios (clearly marked `[SIMULATED]`).

---

## 4. Dependencies & Version Requirements

### Backend (Python 3.11+)
- `strands-agents` (AWS Strands AI Agents SDK)
- `boto3 >= 1.34.0` (AWS SDK for Python)
- `pydantic >= 2.6.0` (Schema validation)
- `fastapi >= 0.110.0` & `uvicorn >= 0.28.0` (Local development API)
- `pytest >= 8.0.0` & `httpx >= 0.27.0` (Automated testing)
- `python-dotenv >= 1.0.0`

### Frontend (Node 24 / npm 11)
- `react >= 18.3.0` & `react-dom >= 18.3.0`
- `vite >= 5.2.0`
- `typescript >= 5.3.0`
- `tailwindcss >= 3.4.0` & `lucide-react` (Accessible UI & icons)
- `react-router-dom >= 6.22.0`
- `leaflet >= 1.9.4` & `react-leaflet >= 4.2.1`

---

## 5. Core Data Models

```typescript
// Incident Entity
interface Incident {
  incident_id: string;               // e.g., "INC-2026-A8F9"
  created_at: string;                // ISO 8601
  updated_at: string;                // ISO 8601
  reporter_name?: string;            // Or "Anonymous Survivor"
  reporter_contact?: string;         // Phone / SMS / Radio
  people_reported: number;           // Strict >= 1 integer
  distress_message: string;          // Original message
  
  // Location
  location_type: 'gps' | 'manual_pin' | 'landmark_only';
  latitude?: number;
  longitude?: number;
  landmark_description: string;
  location_precision: 'exact' | 'approximate' | 'unverified';
  
  // Hazard & Needs
  water_level: 'none' | 'ankle' | 'waist' | 'chest' | 'submerged_roof';
  has_injuries: boolean;
  injuries_description?: string;
  special_needs: string[];           // ["children", "elderly", "mobility_impaired", "medical_devices"]
  
  // Triage & Workflow
  status: 'reported' | 'acknowledged' | 'assigned' | 'in_progress' | 'resolved' | 'cancelled';
  suggested_priority: 'critical' | 'high' | 'medium' | 'low';
  priority_reasons: string[];
  assigned_team_id?: string;
  idempotency_key?: string;
  is_simulated: boolean;             // Mandatory flag
  
  // AI Analysis Metadata
  ai_analysis?: {
    confidence: number;              // Informational only, not probability
    immediate_dangers: string[];
    missing_information: string[];
    recommended_next_steps: string[];
    duplicate_candidates: string[];
    human_review_required: boolean;
    processing_status: 'completed' | 'fallback_rules_only' | 'failed';
  };
}
```

---

## 6. Acceptance Criteria (Testing Matrix)

| # | Scenario | Acceptance Test |
|---|---|---|
| 1 | Valid SOS submission | POST /incidents creates record with unique ID |
| 2 | People count validation | Negative/zero counts rejected with 422 |
| 3 | Landmark without GPS | Stored with location_precision='approximate', no fake lat/lng |
| 4 | Medical emergency flag | Priority evaluated as 'critical' or 'high' deterministically |
| 5 | Accidental duplicate click | Duplicate idempotency_key returns original incident without re-saving |
| 6 | UI confirmation guarantee | Success screen rendered only upon 201/200 server response |
| 7 | Natural language extraction | Strands agent correctly identifies trapped count & hazards |
| 8 | Urgent injury detection | Agent flags human_review_required=True |
| 9 | Missing info detection | Agent flags missing address/phone/water depth |
| 10 | AI error/timeout fallback | Incident preserved; deterministic rules assign priority safely |
| 11 | Dashboard count separation | "People Reported" sum != "Known Reported Incidents" count |
| 12 | Status transition guard | Unacknowledged incident cannot be marked resolved directly |
| 13 | Role authorization guard | Survivor cannot invoke responder dispatch actions |
| 14 | Simulated data labeling | UI badges clearly display [SIMULATED DATA] |

---

## 7. Known Limitations & Disaster Context Boundaries

1. **Cellular Network Limitations:** A web application cannot interrogate cellular base stations or count unregistered mobile handsets without carrier interfaces. Only users reporting through the app/gateway are counted.
2. **GPS Precision:** Heavy rains, indoor flooding, or structural cover degrade GPS accuracy. The platform accepts landmark descriptions as first-class citizens.
3. **AI Boundaries:** The Strands Agent assists triage; it never dispatches teams autonomously, never calculates navigable flood currents without hydrological telemetry, and never marks individuals safe without responder verification.
4. **Cloud Prerequisites:** In local development without configured AWS credentials, the application operates in `APP_MODE=local` with full fidelity and zero network degradation.

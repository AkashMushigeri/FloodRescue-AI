# FloodRescue AI — Hackathon Submission Checklist

**WeMakeDevs × AWS Environmental Hackathon 2026**  
*Track: Heat and Water (Flood-related Disaster Response)*  
*Category: Agents and AI*

---

## 1. Compliance & Deliverables Verification

- [x] **Hackathon Track Alignment:** Directly addresses Heat & Water (flood disaster distress coordination and triage).
- [x] **Category Alignment:** Agents and AI using AWS Strands Agents SDK and Amazon Bedrock.
- [x] **Tagline & Identity:** *"Every Distress Signal Matters. Every Rescue Counts."*
- [x] **Working Full-Stack Application:** Built from scratch with React, Vite, TypeScript, Tailwind CSS, Leaflet, Python FastAPI/Lambda, and DynamoDB adapter.
- [x] **Persistence Verified:** Incidents, Teams, Messages, and Audit Events are stored with idempotency protection.
- [x] **AI Agent Implementation:** AWS Strands Agents SDK integration with strictly controlled tools:
  - `get_incident_details`
  - `search_nearby_incidents`
  - `get_available_rescue_teams`
  - `get_team_details`
  - `summarize_incident`
  - `recommend_priority`
  - `draft_survivor_update`
- [x] **Deterministic Safety Rules:** Automatic `CRITICAL` triage for life-threatening keywords, chest-deep water, trapped minors, and acute medical emergencies.
- [x] **Fail-Safe Fallback:** If Bedrock/cloud model is unavailable, reports are preserved and evaluated via deterministic triage rules (`processing_status: "fallback_rules_only"`).
- [x] **Operations Dashboard (`/responder`):** Complete situational awareness, Leaflet geospatial visualization, priority queues, and human-authorized assignment.
- [x] **Fleet Roster (`/teams`):** Field unit status and active incident sorties.
- [x] **Automated Tests:** 13/13 pytest test suite passing covering all core acceptance criteria.
- [x] **Frontend Production Build:** Vite build passing with 0 TypeScript/bundling errors.
- [x] **No Hardcoded Secrets:** Zero API keys or secrets in repository (`.gitignore` and `.env.example` verified).
- [x] **Honest Disaster Boundaries:** Clear disclosures that cellular base stations cannot be enumerated without telecom APIs, and that simulated demo data is clearly badged `[SIMULATED]`.
- [x] **3-Minute Demo Script:** Prepared in `DEMO_SCRIPT.md`.
- [x] **Documentation Package:**
  - `README.md`
  - `IMPLEMENTATION_PLAN.md`
  - `ARCHITECTURE.md`
  - `API.md`
  - `DEPLOYMENT.md`
  - `TESTING.md`
  - `DEMO_SCRIPT.md`
  - `SUBMISSION_CHECKLIST.md`

---

## 2. Pre-Submission Steps for Participants

1. **GitHub Repository:** Push this repository to public GitHub.
2. **Local/Live Run Verification:** Ensure `.\venv\Scripts\python.exe -m uvicorn backend.api.app:app --port 8000` and `npm run dev` are running smoothly for recording.
3. **Demo Video Recording:** Record a screen recording under 3 minutes following `DEMO_SCRIPT.md`. Upload to YouTube as Unlisted/Public.
4. **AWS Deployment (When Credentials Active):** Run `sam build && sam deploy --guided` from `infrastructure/` per `DEPLOYMENT.md`.
5. **Submit Form:** Enter GitHub URL, YouTube URL, and short writeup before hackathon deadline.

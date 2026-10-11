# FloodRescue AI — API Specification

**Version:** 1.0.0  
**Base URL (Local):** `http://localhost:8000`  
**Base URL (AWS Deployed):** `https://{api-id}.execute-api.{region}.amazonaws.com`

---

## 1. System Endpoints

### `GET /health`
Returns system health, active operational mode, persistence type, and timestamp.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "service": "FloodRescue AI",
  "app_mode": "local",
  "timestamp": "2026-10-10T07:15:00.000000Z",
  "persistence_type": "LocalJsonPersistenceAdapter",
  "is_simulated_mode": true
}
```

---

## 2. Incident Distress Reporting & Triage

### `POST /incidents`
Submit a new emergency flood distress signal. Saves the incident record first, then triggers safety triage and AI analysis.

**Headers:**
- `Content-Type: application/json`
- `X-Idempotency-Key: <optional-client-uuid>` (Optional header; can also be provided in body)

**Request Body:**
```json
{
  "reporter_name": "Meera Sundaram",
  "reporter_contact": "+91 98401 23456",
  "people_reported": 4,
  "distress_message": "Water entered ground floor, chest high. Trapped with 82yo asthma patient and 2 kids. Need boat.",
  "location_type": "gps",
  "latitude": 13.0334,
  "longitude": 80.2182,
  "landmark_description": "Old No 14, 2nd Cross St, Gandhi Nagar, Adyar",
  "location_precision": "exact",
  "water_level": "chest",
  "has_injuries": true,
  "injuries_description": "Elderly patient short on inhaler",
  "special_needs": ["elderly", "children", "medical_devices"],
  "idempotency_key": "sos-client-uuid-9921",
  "is_simulated": true
}
```

**Response `201 Created`:**
```json
{
  "incident_id": "INC-2026-4B82A1",
  "created_at": "2026-10-10T07:15:01.000000Z",
  "updated_at": "2026-10-10T07:15:01.000000Z",
  "reporter_name": "Meera Sundaram",
  "reporter_contact": "+91 98401 23456",
  "people_reported": 4,
  "distress_message": "Water entered ground floor, chest high. Trapped with 82yo asthma patient and 2 kids. Need boat.",
  "location_type": "gps",
  "latitude": 13.0334,
  "longitude": 80.2182,
  "landmark_description": "Old No 14, 2nd Cross St, Gandhi Nagar, Adyar",
  "location_precision": "exact",
  "water_level": "chest",
  "has_injuries": true,
  "injuries_description": "Elderly patient short on inhaler",
  "special_needs": ["elderly", "children", "medical_devices"],
  "status": "reported",
  "suggested_priority": "critical",
  "priority_reasons": [
    "High water level hazard: Chest-deep water reported",
    "Reported injury or medical emergency: Elderly patient short on inhaler",
    "Vulnerable occupants requiring specialized evacuation: elderly, children, medical_devices"
  ],
  "assigned_team_id": null,
  "ai_analysis": {
    "confidence": 0.88,
    "immediate_dangers": ["Rapidly rising chest water", "Asthma crisis"],
    "missing_information": ["Battery backup level for medical device"],
    "recommended_next_steps": ["Dispatch swift water boat squad", "Equip team with portable oxygen"],
    "duplicate_candidates": [],
    "human_review_required": true,
    "suggested_priority": "critical",
    "priority_reasons": ["Chest-deep water", "Critical medical dependency"],
    "summary_for_dashboard": "Adyar: 4 persons trapped. Chest water.",
    "processing_status": "completed"
  },
  "is_simulated": true,
  "data_source": "web"
}
```

---

### `GET /incidents`
Retrieve filterable, paginated distress reports along with operational dashboard metrics.

**Query Parameters:**
- `status` (`reported` | `acknowledged` | `assigned` | `in_progress` | `resolved`)
- `priority` (`critical` | `high` | `medium` | `low`)
- `search` (Search query across landmark, reporter, message, or ID)
- `limit` (Default: 50, Max: 200)
- `offset` (Default: 0)

**Response `200 OK`:**
```json
{
  "items": [ ... ],
  "total": 14,
  "metrics": {
    "people_reported": 48,
    "known_reported_incidents": 14,
    "urgent_review_required": 5,
    "location_verification_needed": 3,
    "assigned_count": 4,
    "resolved_count": 2
  }
}
```

---

### `GET /incidents/{incident_id}`
Retrieve full details of a specific incident.

**Response `200 OK`** or `404 Not Found`.

---

### `PATCH /incidents/{incident_id}`
Update permitted operational fields (e.g., status, landmark refinement, water level).

---

## 3. Operations Workflow & Dispatch Endpoints

### `POST /incidents/{incident_id}/acknowledge`
Acknowledge an emergency distress signal by operations headquarters.

**Query Parameters:**
- `dispatcher_id`: Identifier of acknowledging responder (default: `DISPATCHER-01`)

**Response `200 OK`:** Returns updated `Incident` with status `acknowledged`.

---

### `POST /incidents/{incident_id}/assign`
Assign an authorized rescue team to an incident. Sets incident status to `assigned` and team status to `dispatched`.

**Request Body:**
```json
{
  "team_id": "TEAM-SWIFT-01",
  "dispatcher_id": "DISPATCHER-HQ",
  "dispatch_notes": "Deploy inflatable boat squad with paramedic"
}
```

**Response `200 OK`:** Returns updated `Incident`.

---

### `POST /incidents/{incident_id}/resolve`
Mark an incident resolved once all individuals have been evacuated or verified safe.

**Query Parameters:**
- `resolved_by`: Responder ID
- `resolution_notes`: Optional debrief notes

**Guard Rule:** Cannot resolve an incident that is still in `reported` status without prior acknowledgment or assignment.

---

### `POST /incidents/{incident_id}/analyze`
On-demand execution of the AWS Strands AI triage agent against an existing incident report.

---

## 4. Rescue Teams Management

### `GET /teams`
List authorized response teams with equipment, capability tags, and personnel counts.

### `GET /teams/{team_id}`
Retrieve a specific team's status and assigned incident roster.

### `PATCH /teams/{team_id}/status`
Update field team status (`available` | `dispatched` | `on_scene` | `returning` | `offline`).

---

## 5. Survivor-Dispatch Communication Thread

### `GET /incidents/{incident_id}/messages`
Retrieve communication history between survivor and dispatchers.

### `POST /incidents/{incident_id}/messages`
Add a new follow-up message to the incident thread.

**Request Body:**
```json
{
  "sender_role": "survivor",
  "sender_name": "Meera",
  "message_content": "Water has now risen above the porch steps."
}
```

---

## 6. Demonstration Helper

### `POST /seed-simulated-data`
Seeds realistic simulated flood scenarios across Chennai flood zones (Adyar, Velachery, Nungambakkam) for testing.

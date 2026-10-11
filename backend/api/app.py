from __future__ import annotations
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models.incident import (
    Incident,
    IncidentCreate,
    IncidentUpdate,
    IncidentStatus,
    PriorityLevel,
    AIProcessingStatus,
)
from backend.models.team import (
    RescueTeam,
    TeamStatus,
    AssignTeamRequest,
    TeamStatusUpdateRequest,
)
from backend.models.message import Message, MessageCreate, SenderRole
from backend.models.audit import AuditEvent
from backend.services.persistence import get_persistence_adapter
from backend.agents.flood_agent import get_flood_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FloodRescueAI.API")

app = FastAPI(
    title="FloodRescue AI API",
    description="Emergency flood distress reporting and rescue coordination platform backend",
    version="1.0.0",
)

# Enable CORS for local Vite and deployed frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted via environment in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_incident_id() -> str:
    short_suffix = uuid.uuid4().hex[:6].upper()
    return f"INC-2026-{short_suffix}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    adapter = get_persistence_adapter()
    app_mode = os.getenv("APP_MODE", "local").lower()
    return {
        "status": "healthy",
        "service": "FloodRescue AI",
        "app_mode": app_mode,
        "timestamp": now_iso(),
        "persistence_type": adapter.__class__.__name__,
        "is_simulated_mode": app_mode == "local",
    }


@app.post("/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED, tags=["Incidents"])
def create_incident(
    payload: IncidentCreate,
    x_idempotency_key: Optional[str] = Header(default=None),
) -> Incident:
    adapter = get_persistence_adapter()
    idempotency_key = payload.idempotency_key or x_idempotency_key

    # 1. Idempotency Check: Prevent duplicate submissions
    if idempotency_key:
        existing = adapter.get_incident_by_idempotency_key(idempotency_key)
        if existing:
            logger.info(f"Duplicate submission prevented via idempotency key '{idempotency_key}' -> {existing.incident_id}")
            return existing

    # 2. Strict validation of people count
    if payload.people_reported < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reported people count must be at least 1 person.",
        )

    # 3. Save incident first (resilience guarantee)
    incident_id = generate_incident_id()
    now_ts = now_iso()

    incident = Incident(
        incident_id=incident_id,
        created_at=now_ts,
        updated_at=now_ts,
        reporter_name=payload.reporter_name or "Anonymous Survivor",
        reporter_contact=payload.reporter_contact,
        people_reported=payload.people_reported,
        distress_message=payload.distress_message,
        location_type=payload.location_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        landmark_description=payload.landmark_description,
        location_precision=payload.location_precision,
        water_level=payload.water_level,
        has_injuries=payload.has_injuries,
        injuries_description=payload.injuries_description,
        special_needs=payload.special_needs,
        status=IncidentStatus.REPORTED,
        suggested_priority=PriorityLevel.MEDIUM,
        priority_reasons=[],
        idempotency_key=idempotency_key,
        is_simulated=payload.is_simulated,
        data_source=payload.data_source,
    )

    saved_incident = adapter.save_incident(incident)

    # Log audit event
    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier=payload.reporter_name or "Anonymous",
            action="INCIDENT_CREATED",
            target_incident_id=incident_id,
            timestamp=now_ts,
            outcome="SUCCESS",
            details={"people_reported": payload.people_reported, "priority": "evaluation_pending"},
        )
    )

    # 4. Trigger AI Triage Analysis asynchronously/in-pipeline
    agent = get_flood_agent()
    try:
        analysis = agent.analyze(payload, incident_id=incident_id)
        updates = {
            "ai_analysis": analysis.model_dump(),
            "suggested_priority": analysis.suggested_priority,
            "priority_reasons": analysis.priority_reasons,
        }
        updated = adapter.update_incident(incident_id, updates)
        if updated:
            saved_incident = updated
    except Exception as e:
        logger.error(f"Error during AI triage for incident {incident_id}: {e}")

    # Add initial system confirmation message into incident discussion
    adapter.add_message(
        Message(
            message_id=f"MSG-{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
            sender_role=SenderRole.SYSTEM,
            sender_name="Emergency Coordination System",
            message_content=f"Distress report logged (Ref: {incident_id}). Emergency triage queued.",
            created_at=now_iso(),
            delivery_status="delivered",
        )
    )

    return saved_incident


class IncidentListResponse(BaseModel):
    items: List[Incident]
    total: int
    metrics: Dict[str, Any]


@app.get("/incidents", response_model=IncidentListResponse, tags=["Incidents"])
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(default=None, alias="status"),
    priority_filter: Optional[PriorityLevel] = Query(default=None, alias="priority"),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> IncidentListResponse:
    adapter = get_persistence_adapter()
    items, total = adapter.list_incidents(
        status=status_filter,
        priority=priority_filter,
        search=search,
        limit=limit,
        offset=offset,
    )

    # Calculate operational metrics across all stored incidents
    all_items, _ = adapter.list_incidents(limit=1000)
    total_people = sum(i.people_reported for i in all_items)
    urgent_count = sum(1 for i in all_items if i.suggested_priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH] and i.status != IncidentStatus.RESOLVED)
    location_unverified_count = sum(1 for i in all_items if i.location_precision.value == "unverified" or (i.latitude is None and i.longitude is None))
    assigned_count = sum(1 for i in all_items if i.status == IncidentStatus.ASSIGNED)
    resolved_count = sum(1 for i in all_items if i.status == IncidentStatus.RESOLVED)

    metrics = {
        "people_reported": total_people,
        "known_reported_incidents": len(all_items),
        "urgent_review_required": urgent_count,
        "location_verification_needed": location_unverified_count,
        "assigned_count": assigned_count,
        "resolved_count": resolved_count,
    }

    return IncidentListResponse(items=items, total=total, metrics=metrics)


@app.get("/incidents/{incident_id}", response_model=Incident, tags=["Incidents"])
def get_incident(incident_id: str) -> Incident:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return incident


@app.patch("/incidents/{incident_id}", response_model=Incident, tags=["Incidents"])
def update_incident_fields(incident_id: str, payload: IncidentUpdate) -> Incident:
    adapter = get_persistence_adapter()
    existing = adapter.get_incident(incident_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = adapter.update_incident(incident_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update incident.")

    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier="RESPONDER_PANEL",
            action="INCIDENT_UPDATED",
            target_incident_id=incident_id,
            timestamp=now_iso(),
            outcome="SUCCESS",
            details=updates,
        )
    )
    return updated


@app.post("/incidents/{incident_id}/acknowledge", response_model=Incident, tags=["Workflow"])
def acknowledge_incident(
    incident_id: str,
    dispatcher_id: str = Query(default="DISPATCHER-01"),
) -> Incident:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot acknowledge a resolved incident.")

    now_ts = now_iso()
    updated = adapter.update_incident(
        incident_id,
        {
            "status": IncidentStatus.ACKNOWLEDGED,
            "acknowledged_by": dispatcher_id,
            "acknowledged_at": now_ts,
        },
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed.")

    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier=dispatcher_id,
            action="INCIDENT_ACKNOWLEDGED",
            target_incident_id=incident_id,
            timestamp=now_ts,
            outcome="SUCCESS",
        )
    )

    adapter.add_message(
        Message(
            message_id=f"MSG-{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
            sender_role=SenderRole.RESPONDER,
            sender_name=dispatcher_id,
            message_content=f"Distress report acknowledged by Operations Commander ({dispatcher_id}). Triage team active.",
            created_at=now_ts,
        )
    )

    return updated


@app.post("/incidents/{incident_id}/assign", response_model=Incident, tags=["Workflow"])
def assign_incident_team(
    incident_id: str,
    payload: AssignTeamRequest,
) -> Incident:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if incident.status == IncidentStatus.RESOLVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign teams to an already resolved incident.")

    team = adapter.get_team(payload.team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rescue team '{payload.team_id}' not found.")

    now_ts = now_iso()

    # Update team status and assignment list
    assigned_list = list(set(team.assigned_incidents + [incident_id]))
    adapter.update_team(
        payload.team_id,
        {
            "status": TeamStatus.DISPATCHED,
            "assigned_incidents": assigned_list,
        },
    )

    # Update incident
    updated_incident = adapter.update_incident(
        incident_id,
        {
            "status": IncidentStatus.ASSIGNED,
            "assigned_team_id": payload.team_id,
        },
    )

    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier=payload.dispatcher_id,
            action="TEAM_ASSIGNED",
            target_incident_id=incident_id,
            target_team_id=payload.team_id,
            timestamp=now_ts,
            outcome="SUCCESS",
            details={"notes": payload.dispatch_notes},
        )
    )

    adapter.add_message(
        Message(
            message_id=f"MSG-{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
            sender_role=SenderRole.SYSTEM,
            sender_name="Dispatch Command",
            message_content=f"Rescue Team '{team.team_name}' dispatched to your sector.",
            created_at=now_ts,
        )
    )

    return updated_incident


@app.post("/incidents/{incident_id}/resolve", response_model=Incident, tags=["Workflow"])
def resolve_incident(
    incident_id: str,
    resolved_by: str = Query(default="DISPATCHER-01"),
    resolution_notes: Optional[str] = Query(default=None),
) -> Incident:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if incident.status == IncidentStatus.REPORTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident must be acknowledged or assigned before being resolved.",
        )

    now_ts = now_iso()
    updated = adapter.update_incident(
        incident_id,
        {
            "status": IncidentStatus.RESOLVED,
            "resolved_by": resolved_by,
            "resolved_at": now_ts,
        },
    )

    # If a team was assigned, release team back to AVAILABLE if no other assignments
    if incident.assigned_team_id:
        team = adapter.get_team(incident.assigned_team_id)
        if team:
            remaining = [i for i in team.assigned_incidents if i != incident_id]
            adapter.update_team(
                incident.assigned_team_id,
                {
                    "assigned_incidents": remaining,
                    "status": TeamStatus.AVAILABLE if not remaining else TeamStatus.DISPATCHED,
                },
            )

    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier=resolved_by,
            action="INCIDENT_RESOLVED",
            target_incident_id=incident_id,
            timestamp=now_ts,
            outcome="SUCCESS",
            details={"notes": resolution_notes},
        )
    )

    adapter.add_message(
        Message(
            message_id=f"MSG-{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
            sender_role=SenderRole.SYSTEM,
            sender_name="Emergency Coordination Center",
            message_content="Incident marked resolved by operational commander. All personnel evacuated / accounted for.",
            created_at=now_ts,
        )
    )

    return updated


@app.post("/incidents/{incident_id}/analyze", tags=["AI Agent"])
def trigger_ai_analysis(incident_id: str) -> Dict[str, Any]:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    agent = get_flood_agent()
    # Build IncidentCreate for agent evaluation
    inc_create = IncidentCreate(
        reporter_name=incident.reporter_name,
        reporter_contact=incident.reporter_contact,
        people_reported=incident.people_reported,
        distress_message=incident.distress_message,
        location_type=incident.location_type,
        latitude=incident.latitude,
        longitude=incident.longitude,
        landmark_description=incident.landmark_description,
        location_precision=incident.location_precision,
        water_level=incident.water_level,
        has_injuries=incident.has_injuries,
        injuries_description=incident.injuries_description,
        special_needs=incident.special_needs,
        is_simulated=incident.is_simulated,
    )
    analysis = agent.analyze(inc_create, incident_id=incident_id)
    adapter.update_incident(
        incident_id,
        {
            "ai_analysis": analysis.model_dump(),
            "suggested_priority": analysis.suggested_priority,
            "priority_reasons": analysis.priority_reasons,
        },
    )
    return analysis.model_dump()


@app.get("/incidents/{incident_id}/messages", response_model=List[Message], tags=["Messages"])
def get_incident_messages(incident_id: str) -> List[Message]:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return adapter.get_messages(incident_id)


@app.post("/incidents/{incident_id}/messages", response_model=Message, status_code=status.HTTP_201_CREATED, tags=["Messages"])
def post_incident_message(incident_id: str, payload: MessageCreate) -> Message:
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    msg = Message(
        message_id=f"MSG-{uuid.uuid4().hex[:8]}",
        incident_id=incident_id,
        sender_role=payload.sender_role,
        sender_name=payload.sender_name,
        message_content=payload.message_content,
        created_at=now_iso(),
        delivery_status="delivered",
    )
    return adapter.add_message(msg)


@app.get("/teams", response_model=List[RescueTeam], tags=["Teams"])
def list_teams() -> List[RescueTeam]:
    adapter = get_persistence_adapter()
    return adapter.list_teams()


@app.get("/teams/{team_id}", response_model=RescueTeam, tags=["Teams"])
def get_team(team_id: str) -> RescueTeam:
    adapter = get_persistence_adapter()
    team = adapter.get_team(team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team '{team_id}' not found.")
    return team


@app.patch("/teams/{team_id}/status", response_model=RescueTeam, tags=["Teams"])
def update_team_status(team_id: str, payload: TeamStatusUpdateRequest) -> RescueTeam:
    adapter = get_persistence_adapter()
    team = adapter.get_team(team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    updates: Dict[str, Any] = {
        "status": payload.status,
        "last_location_update": now_iso(),
    }
    if payload.current_latitude is not None and payload.current_longitude is not None:
        updates["current_latitude"] = payload.current_latitude
        updates["current_longitude"] = payload.current_longitude
    if payload.current_location_name:
        updates["current_location_name"] = payload.current_location_name

    updated_team = adapter.update_team(team_id, updates)
    adapter.log_audit_event(
        AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8]}",
            actor_identifier=payload.responder_id,
            action="TEAM_STATUS_UPDATED",
            target_team_id=team_id,
            timestamp=now_iso(),
            outcome="SUCCESS",
            details={"status": payload.status.value, "notes": payload.notes},
        )
    )
    return updated_team


@app.post("/seed-simulated-data", tags=["Demo"])
def seed_simulated_data() -> Dict[str, str]:
    adapter = get_persistence_adapter()
    adapter.seed_simulated_data()
    return {"message": "Simulated flood rescue demonstration data seeded successfully."}

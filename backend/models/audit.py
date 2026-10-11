from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event_id: str
    actor_identifier: str = Field(description="User ID, Dispatcher ID, or System Agent")
    action: str = Field(description="e.g. INCIDENT_CREATED, INCIDENT_ACKNOWLEDGED, TEAM_ASSIGNED")
    target_incident_id: Optional[str] = None
    target_team_id: Optional[str] = None
    timestamp: str
    outcome: str = "SUCCESS"
    details: Dict[str, Any] = Field(default_factory=dict)

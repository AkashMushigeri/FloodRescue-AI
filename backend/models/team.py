from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TeamStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    ON_SCENE = "on_scene"
    RETURNING = "returning"
    OFFLINE = "offline"


class RescueTeam(BaseModel):
    team_id: str
    team_name: str
    personnel_count: int = Field(ge=1)
    status: TeamStatus = TeamStatus.AVAILABLE
    capabilities: List[str] = Field(default_factory=list)
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location_name: str = "Staging Area Alpha"
    assigned_incidents: List[str] = Field(default_factory=list)
    last_location_update: str
    contact_channel: str = "VHF-CH-16 / SAT-02"
    is_simulated: bool = True


class AssignTeamRequest(BaseModel):
    team_id: str
    dispatcher_id: str = "DISPATCHER-01"
    dispatch_notes: Optional[str] = None


class TeamStatusUpdateRequest(BaseModel):
    status: TeamStatus
    responder_id: str
    notes: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location_name: Optional[str] = None

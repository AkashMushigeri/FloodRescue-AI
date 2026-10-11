from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LocationType(str, Enum):
    GPS = "gps"
    MANUAL_PIN = "manual_pin"
    LANDMARK_ONLY = "landmark_only"


class LocationPrecision(str, Enum):
    EXACT = "exact"              # High-accuracy GPS (< 25m)
    APPROXIMATE = "approximate"  # Manual pin or landmark description
    UNVERIFIED = "unverified"    # General locality, street name only


class WaterLevel(str, Enum):
    NONE = "none"
    ANKLE = "ankle"
    WAIST = "waist"
    CHEST = "chest"
    SUBMERGED_ROOF = "submerged_roof"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    CRITICAL = "critical"  # Immediate threat to life / medical crisis / trapped rising water
    HIGH = "high"          # Rising water, vulnerable people (infants/elderly), urgent medical
    MEDIUM = "medium"      # Safe temporarily (high ground/roof), stable needs
    LOW = "low"            # Property hazard, advisory, non-immediate distress


class AIProcessingStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FALLBACK_RULES_ONLY = "fallback_rules_only"
    FAILED = "failed"


class AIAnalysisResult(BaseModel):
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Informational model confidence score")
    immediate_dangers: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    duplicate_candidates: List[str] = Field(default_factory=list)
    human_review_required: bool = True
    suggested_priority: PriorityLevel = PriorityLevel.MEDIUM
    priority_reasons: List[str] = Field(default_factory=list)
    summary_for_dashboard: str = ""
    processing_status: AIProcessingStatus = AIProcessingStatus.PENDING
    model_name: Optional[str] = None
    processed_at: Optional[str] = None


class IncidentCreate(BaseModel):
    reporter_name: Optional[str] = Field(default="Anonymous Survivor", max_length=100)
    reporter_contact: Optional[str] = Field(default=None, max_length=100)
    people_reported: int = Field(ge=1, le=1000, description="Strict number of people reported in this distress call")
    distress_message: str = Field(min_length=3, max_length=2000, description="Detailed distress message")
    
    # Location
    location_type: LocationType = LocationType.LANDMARK_ONLY
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    landmark_description: str = Field(min_length=2, max_length=500, description="Physical address, landmark, or floor level")
    location_precision: LocationPrecision = LocationPrecision.APPROXIMATE
    
    # Hazard details
    water_level: WaterLevel = WaterLevel.NONE
    has_injuries: bool = False
    injuries_description: Optional[str] = Field(default=None, max_length=500)
    special_needs: List[str] = Field(default_factory=list, description="e.g. infants, elderly, mobility_impaired, oxygen, diabetic")
    
    # Control flags
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    is_simulated: bool = Field(default=True, description="Explicit flag indicating simulated or real data")
    data_source: str = Field(default="web", max_length=50)

    @field_validator("people_reported")
    @classmethod
    def validate_people(cls, v: int) -> int:
        if v < 1:
            raise ValueError("People reported must be at least 1")
        return v


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    assigned_team_id: Optional[str] = None
    suggested_priority: Optional[PriorityLevel] = None
    landmark_description: Optional[str] = None
    water_level: Optional[WaterLevel] = None
    has_injuries: Optional[bool] = None
    injuries_description: Optional[str] = None


class Incident(BaseModel):
    incident_id: str
    created_at: str
    updated_at: str
    reporter_name: str
    reporter_contact: Optional[str] = None
    people_reported: int
    distress_message: str
    
    # Location
    location_type: LocationType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark_description: str
    location_precision: LocationPrecision
    
    # Hazard details
    water_level: WaterLevel
    has_injuries: bool
    injuries_description: Optional[str] = None
    special_needs: List[str] = Field(default_factory=list)
    
    # Operations status
    status: IncidentStatus = IncidentStatus.REPORTED
    suggested_priority: PriorityLevel = PriorityLevel.MEDIUM
    priority_reasons: List[str] = Field(default_factory=list)
    assigned_team_id: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    
    # AI & Meta
    ai_analysis: Optional[AIAnalysisResult] = None
    idempotency_key: Optional[str] = None
    is_simulated: bool = True
    data_source: str = "web"

from __future__ import annotations
import json
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from backend.models.incident import (
    Incident,
    IncidentStatus,
    PriorityLevel,
    LocationType,
    LocationPrecision,
    WaterLevel,
    AIProcessingStatus,
    AIAnalysisResult,
)
from backend.models.team import RescueTeam, TeamStatus
from backend.models.message import Message, SenderRole
from backend.models.audit import AuditEvent


class PersistenceAdapter(ABC):
    @abstractmethod
    def save_incident(self, incident: Incident) -> Incident:
        pass

    @abstractmethod
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        pass

    @abstractmethod
    def get_incident_by_idempotency_key(self, idempotency_key: str) -> Optional[Incident]:
        pass

    @abstractmethod
    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        priority: Optional[PriorityLevel] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Incident], int]:
        pass

    @abstractmethod
    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Incident]:
        pass

    @abstractmethod
    def save_team(self, team: RescueTeam) -> RescueTeam:
        pass

    @abstractmethod
    def get_team(self, team_id: str) -> Optional[RescueTeam]:
        pass

    @abstractmethod
    def list_teams(self) -> List[RescueTeam]:
        pass

    @abstractmethod
    def update_team(self, team_id: str, updates: Dict[str, Any]) -> Optional[RescueTeam]:
        pass

    @abstractmethod
    def add_message(self, message: Message) -> Message:
        pass

    @abstractmethod
    def get_messages(self, incident_id: str) -> List[Message]:
        pass

    @abstractmethod
    def log_audit_event(self, event: AuditEvent) -> None:
        pass

    @abstractmethod
    def get_audit_events(self, limit: int = 50) -> List[AuditEvent]:
        pass

    @abstractmethod
    def seed_simulated_data(self) -> None:
        pass


class LocalJsonPersistenceAdapter(PersistenceAdapter):
    """Deterministic local persistence adapter storing JSON on disk."""

    def __init__(self, file_path: str = "data/local_db.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_storage()

    def _init_storage(self) -> None:
        with self._lock:
            if not self.file_path.exists():
                initial_data = {
                    "incidents": {},
                    "teams": {},
                    "messages": {},
                    "audit_events": [],
                    "idempotency_keys": {},
                }
                self.file_path.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")
                self._seed_default_teams_locked()

    def _read_data(self) -> Dict[str, Any]:
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "incidents": {},
                "teams": {},
                "messages": {},
                "audit_events": [],
                "idempotency_keys": {},
            }

    def _write_data(self, data: Dict[str, Any]) -> None:
        self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _seed_default_teams_locked(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        default_teams = [
            RescueTeam(
                team_id="TEAM-SWIFT-01",
                team_name="Swift Water Rescue Unit 1 [SIMULATED]",
                personnel_count=6,
                status=TeamStatus.AVAILABLE,
                capabilities=["swift_water_boats", "paramedic", "night_operations", "thermal_imaging"],
                current_latitude=13.0827,
                current_longitude=80.2707,
                current_location_name="Chennai North Staging Hub",
                last_location_update=now,
                contact_channel="VHF CH-16 (Tac 1)",
                is_simulated=True,
            ),
            RescueTeam(
                team_id="TEAM-BOAT-02",
                team_name="Inflatable Boat Squad Bravo [SIMULATED]",
                personnel_count=4,
                status=TeamStatus.AVAILABLE,
                capabilities=["shallow_draft_boats", "life_rafts", "first_aid"],
                current_latitude=13.0475,
                current_longitude=80.2090,
                current_location_name="Kotturpuram River Relief Post",
                last_location_update=now,
                contact_channel="VHF CH-09 (Tac 2)",
                is_simulated=True,
            ),
            RescueTeam(
                team_id="TEAM-HIGHWATER-03",
                team_name="High-Axle Truck Unit 3 [SIMULATED]",
                personnel_count=5,
                status=TeamStatus.AVAILABLE,
                capabilities=["high_clearance_4x4", "evac_transport_20pax", "generator_lighting"],
                current_latitude=13.0012,
                current_longitude=80.2565,
                current_location_name="Adyar Depot Staging Point",
                last_location_update=now,
                contact_channel="VHF CH-12 (Tac 3)",
                is_simulated=True,
            ),
            RescueTeam(
                team_id="TEAM-MEDEVAC-04",
                team_name="Disaster Medical Evac 4 [SIMULATED]",
                personnel_count=4,
                status=TeamStatus.AVAILABLE,
                capabilities=["critical_care_paramedic", "portable_ventilator", "trauma_kits"],
                current_latitude=13.0604,
                current_longitude=80.2496,
                current_location_name="Central General Hospital Relief Base",
                last_location_update=now,
                contact_channel="VHF CH-14 (Medical)",
                is_simulated=True,
            ),
        ]
        data = self._read_data()
        for t in default_teams:
            data["teams"][t.team_id] = t.model_dump()
        self._write_data(data)

    def save_incident(self, incident: Incident) -> Incident:
        with self._lock:
            data = self._read_data()
            data["incidents"][incident.incident_id] = incident.model_dump()
            if incident.idempotency_key:
                data["idempotency_keys"][incident.idempotency_key] = incident.incident_id
            self._write_data(data)
            return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._lock:
            data = self._read_data()
            raw = data["incidents"].get(incident_id)
            if raw:
                return Incident.model_validate(raw)
            return None

    def get_incident_by_idempotency_key(self, idempotency_key: str) -> Optional[Incident]:
        with self._lock:
            data = self._read_data()
            incident_id = data.get("idempotency_keys", {}).get(idempotency_key)
            if incident_id and incident_id in data["incidents"]:
                return Incident.model_validate(data["incidents"][incident_id])
            return None

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        priority: Optional[PriorityLevel] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Incident], int]:
        with self._lock:
            data = self._read_data()
            items = [Incident.model_validate(item) for item in data["incidents"].values()]

            if status:
                items = [i for i in items if i.status == status]
            if priority:
                items = [i for i in items if i.suggested_priority == priority]
            if search:
                s_lower = search.lower()
                items = [
                    i
                    for i in items
                    if s_lower in i.incident_id.lower()
                    or s_lower in i.landmark_description.lower()
                    or s_lower in i.distress_message.lower()
                    or s_lower in i.reporter_name.lower()
                ]

            # Sort: newest first
            items.sort(key=lambda x: x.created_at, reverse=True)
            total = len(items)
            paginated = items[offset : offset + limit]
            return paginated, total

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Incident]:
        with self._lock:
            data = self._read_data()
            raw = data["incidents"].get(incident_id)
            if not raw:
                return None
            raw.update(updates)
            raw["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated_incident = Incident.model_validate(raw)
            data["incidents"][incident_id] = updated_incident.model_dump()
            self._write_data(data)
            return updated_incident

    def save_team(self, team: RescueTeam) -> RescueTeam:
        with self._lock:
            data = self._read_data()
            data["teams"][team.team_id] = team.model_dump()
            self._write_data(data)
            return team

    def get_team(self, team_id: str) -> Optional[RescueTeam]:
        with self._lock:
            data = self._read_data()
            raw = data["teams"].get(team_id)
            if raw:
                return RescueTeam.model_validate(raw)
            return None

    def list_teams(self) -> List[RescueTeam]:
        with self._lock:
            data = self._read_data()
            return [RescueTeam.model_validate(t) for t in data["teams"].values()]

    def update_team(self, team_id: str, updates: Dict[str, Any]) -> Optional[RescueTeam]:
        with self._lock:
            data = self._read_data()
            raw = data["teams"].get(team_id)
            if not raw:
                return None
            raw.update(updates)
            updated_team = RescueTeam.model_validate(raw)
            data["teams"][team_id] = updated_team.model_dump()
            self._write_data(data)
            return updated_team

    def add_message(self, message: Message) -> Message:
        with self._lock:
            data = self._read_data()
            if message.incident_id not in data["messages"]:
                data["messages"][message.incident_id] = []
            data["messages"][message.incident_id].append(message.model_dump())
            self._write_data(data)
            return message

    def get_messages(self, incident_id: str) -> List[Message]:
        with self._lock:
            data = self._read_data()
            raw_list = data["messages"].get(incident_id, [])
            return [Message.model_validate(m) for m in raw_list]

    def log_audit_event(self, event: AuditEvent) -> None:
        with self._lock:
            data = self._read_data()
            data["audit_events"].append(event.model_dump())
            # Keep last 500 events
            if len(data["audit_events"]) > 500:
                data["audit_events"] = data["audit_events"][-500:]
            self._write_data(data)

    def get_audit_events(self, limit: int = 50) -> List[AuditEvent]:
        with self._lock:
            data = self._read_data()
            events = [AuditEvent.model_validate(e) for e in data["audit_events"]]
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]

    def seed_simulated_data(self) -> None:
        with self._lock:
            self._seed_default_teams_locked()
            now = datetime.now(timezone.utc).isoformat()
            simulated_incidents = [
                Incident(
                    incident_id="INC-2026-SIM-01",
                    created_at=now,
                    updated_at=now,
                    reporter_name="Meera Sundaram [SIMULATED]",
                    reporter_contact="+91 98401 23456",
                    people_reported=4,
                    distress_message="Water entered 1st floor. Chest high in driveway. Elderly grandmother with asthma and 2 young children. Electricity cut off. Need boat evacuation urgently.",
                    location_type=LocationType.GPS,
                    latitude=13.0334,
                    longitude=80.2182,
                    landmark_description="Old No 14, 2nd Cross St, Gandhi Nagar, Adyar (near Fortis Malar)",
                    location_precision=LocationPrecision.EXACT,
                    water_level=WaterLevel.CHEST,
                    has_injuries=True,
                    injuries_description="Asthma patient running low on inhaler / oxygen",
                    special_needs=["elderly", "children", "medical_devices"],
                    status=IncidentStatus.REPORTED,
                    suggested_priority=PriorityLevel.CRITICAL,
                    priority_reasons=[
                        "Immediate threat to life: chest-deep rising water",
                        "Vulnerable occupants: elderly with asthma requiring oxygen",
                        "2 young children trapped without electricity",
                    ],
                    ai_analysis=AIAnalysisResult(
                        confidence=0.92,
                        immediate_dangers=["Rapidly rising chest-high water", "Power outage", "Asthma crisis"],
                        missing_information=["Battery backup level for medical device"],
                        recommended_next_steps=["Dispatch Swift Water Boat Squad immediately", "Equip team with portable oxygen inhaler"],
                        human_review_required=True,
                        suggested_priority=PriorityLevel.CRITICAL,
                        priority_reasons=["Chest-deep water", "Critical medical dependency", "Trapped minors"],
                        summary_for_dashboard="Adyar: 4 persons trapped (elderly asthma patient + 2 kids). Chest water.",
                        processing_status=AIProcessingStatus.COMPLETED,
                    ),
                    is_simulated=True,
                    data_source="simulated_seed",
                ),
                Incident(
                    incident_id="INC-2026-SIM-02",
                    created_at=now,
                    updated_at=now,
                    reporter_name="Ramesh Kumar [SIMULATED]",
                    reporter_contact="+91 97910 88776",
                    people_reported=6,
                    distress_message="Apartment ground floor flooded up to waist level. Moving up to terrace. 6 adults safe for next few hours but drinking water exhausted.",
                    location_type=LocationType.MANUAL_PIN,
                    latitude=13.0645,
                    longitude=80.2450,
                    landmark_description="Green Meadows Apts, Nungambakkam High Rd, Opp Police Station",
                    location_precision=LocationPrecision.APPROXIMATE,
                    water_level=WaterLevel.WAIST,
                    has_injuries=False,
                    special_needs=[],
                    status=IncidentStatus.ACKNOWLEDGED,
                    suggested_priority=PriorityLevel.MEDIUM,
                    priority_reasons=["Ground floor waist water", "Safe on terrace currently", "Supply replenishment required"],
                    acknowledged_by="DISPATCHER-01",
                    acknowledged_at=now,
                    ai_analysis=AIAnalysisResult(
                        confidence=0.88,
                        immediate_dangers=["Waist-level inundation on lower floors"],
                        missing_information=["Terrace accessibility and structural stability"],
                        recommended_next_steps=["Queue for ration and water drop or high-axle truck evacuation"],
                        human_review_required=False,
                        suggested_priority=PriorityLevel.MEDIUM,
                        priority_reasons=["Occupants on terrace, immediate life threat is mitigated"],
                        summary_for_dashboard="Nungambakkam: 6 adults safe on terrace. Waist water on ground floor. Needs water rations.",
                        processing_status=AIProcessingStatus.COMPLETED,
                    ),
                    is_simulated=True,
                    data_source="simulated_seed",
                ),
                Incident(
                    incident_id="INC-2026-SIM-03",
                    created_at=now,
                    updated_at=now,
                    reporter_name="Karthik V [SIMULATED]",
                    reporter_contact=None,
                    people_reported=2,
                    distress_message="Car stalled in underpass near Velachery railway station. Water rising past tires quickly. Cannot open doors easily.",
                    location_type=LocationType.LANDMARK_ONLY,
                    latitude=12.9815,
                    longitude=80.2180,
                    landmark_description="Velachery MRTS station subway bridge",
                    location_precision=LocationPrecision.APPROXIMATE,
                    water_level=WaterLevel.WAIST,
                    has_injuries=False,
                    special_needs=[],
                    status=IncidentStatus.ASSIGNED,
                    assigned_team_id="TEAM-SWIFT-01",
                    suggested_priority=PriorityLevel.HIGH,
                    priority_reasons=["Trapped vehicle in submerged underpass", "Rapidly rising flash flood"],
                    is_simulated=True,
                    data_source="simulated_seed",
                ),
            ]
            data = self._read_data()
            for inc in simulated_incidents:
                data["incidents"][inc.incident_id] = inc.model_dump()
            self._write_data(data)


_adapter_instance: Optional[PersistenceAdapter] = None


def get_persistence_adapter() -> PersistenceAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        app_mode = os.getenv("APP_MODE", "local").lower()
        if app_mode == "aws":
            # Lazy import to avoid boto3 requirement in local mode
            try:
                from backend.services.dynamodb_persistence import DynamoDbPersistenceAdapter
                _adapter_instance = DynamoDbPersistenceAdapter()
            except Exception as e:
                print(f"[WARNING] Could not initialize DynamoDB adapter: {e}. Falling back to LocalJsonPersistenceAdapter.")
                _adapter_instance = LocalJsonPersistenceAdapter()
        else:
            _adapter_instance = LocalJsonPersistenceAdapter()
    return _adapter_instance

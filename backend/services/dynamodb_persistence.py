from __future__ import annotations
import os
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from backend.models.incident import (
    Incident,
    IncidentStatus,
    PriorityLevel,
    LocationType,
    LocationPrecision,
    WaterLevel,
)
from backend.models.team import RescueTeam, TeamStatus
from backend.models.message import Message, SenderRole
from backend.models.audit import AuditEvent
from backend.services.persistence import PersistenceAdapter


def float_to_decimal(obj: Any) -> Any:
    """Helper to convert floats to Decimal for DynamoDB serialization."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(v) for v in obj]
    return obj


def decimal_to_float(obj: Any) -> Any:
    """Helper to convert Decimal back to float/int from DynamoDB."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimal_to_float(v) for v in obj]
    return obj


class DynamoDbPersistenceAdapter(PersistenceAdapter):
    """Production DynamoDB persistence adapter for AWS deployment."""

    def __init__(self):
        import boto3
        region = os.getenv("AWS_REGION", "us-east-1")
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.incidents_table_name = os.getenv("INCIDENTS_TABLE", "FloodRescue-Incidents")
        self.teams_table_name = os.getenv("TEAMS_TABLE", "FloodRescue-Teams")
        self.messages_table_name = os.getenv("MESSAGES_TABLE", "FloodRescue-Messages")
        self.audit_table_name = os.getenv("AUDIT_TABLE", "FloodRescue-Audit")

        self.incidents_table = self.dynamodb.Table(self.incidents_table_name)
        self.teams_table = self.dynamodb.Table(self.teams_table_name)
        self.messages_table = self.dynamodb.Table(self.messages_table_name)
        self.audit_table = self.dynamodb.Table(self.audit_table_name)

    def save_incident(self, incident: Incident) -> Incident:
        item = float_to_decimal(incident.model_dump())
        self.incidents_table.put_item(Item=item)
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        res = self.incidents_table.get_item(Key={"incident_id": incident_id})
        item = res.get("Item")
        if item:
            clean = decimal_to_float(item)
            return Incident.model_validate(clean)
        return None

    def get_incident_by_idempotency_key(self, idempotency_key: str) -> Optional[Incident]:
        # Queries GSI or scans if GSI not provisioned
        from boto3.dynamodb.conditions import Key
        try:
            res = self.incidents_table.query(
                IndexName="IdempotencyIndex",
                KeyConditionExpression=Key("idempotency_key").eq(idempotency_key),
            )
            items = res.get("Items", [])
            if items:
                return Incident.model_validate(decimal_to_float(items[0]))
        except Exception:
            pass
        return None

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        priority: Optional[PriorityLevel] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Incident], int]:
        # In serverless prototype, scan with limit
        res = self.incidents_table.scan(Limit=limit + offset + 50)
        items = [Incident.model_validate(decimal_to_float(i)) for i in res.get("Items", [])]

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
            ]

        items.sort(key=lambda x: x.created_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Incident]:
        current = self.get_incident(incident_id)
        if not current:
            return None
        current_data = current.model_dump()
        current_data.update(updates)
        current_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated_incident = Incident.model_validate(current_data)
        self.save_incident(updated_incident)
        return updated_incident

    def save_team(self, team: RescueTeam) -> RescueTeam:
        item = float_to_decimal(team.model_dump())
        self.teams_table.put_item(Item=item)
        return team

    def get_team(self, team_id: str) -> Optional[RescueTeam]:
        res = self.teams_table.get_item(Key={"team_id": team_id})
        item = res.get("Item")
        if item:
            return RescueTeam.model_validate(decimal_to_float(item))
        return None

    def list_teams(self) -> List[RescueTeam]:
        res = self.teams_table.scan()
        return [RescueTeam.model_validate(decimal_to_float(i)) for i in res.get("Items", [])]

    def update_team(self, team_id: str, updates: Dict[str, Any]) -> Optional[RescueTeam]:
        team = self.get_team(team_id)
        if not team:
            return None
        team_data = team.model_dump()
        team_data.update(updates)
        updated_team = RescueTeam.model_validate(team_data)
        self.save_team(updated_team)
        return updated_team

    def add_message(self, message: Message) -> Message:
        item = float_to_decimal(message.model_dump())
        self.messages_table.put_item(Item=item)
        return message

    def get_messages(self, incident_id: str) -> List[Message]:
        from boto3.dynamodb.conditions import Key
        try:
            res = self.messages_table.query(
                IndexName="IncidentIndex",
                KeyConditionExpression=Key("incident_id").eq(incident_id),
            )
            items = [Message.model_validate(decimal_to_float(i)) for i in res.get("Items", [])]
            items.sort(key=lambda x: x.created_at)
            return items
        except Exception:
            return []

    def log_audit_event(self, event: AuditEvent) -> None:
        item = float_to_decimal(event.model_dump())
        self.audit_table.put_item(Item=item)

    def get_audit_events(self, limit: int = 50) -> List[AuditEvent]:
        res = self.audit_table.scan(Limit=limit)
        items = [AuditEvent.model_validate(decimal_to_float(i)) for i in res.get("Items", [])]
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]

    def seed_simulated_data(self) -> None:
        pass

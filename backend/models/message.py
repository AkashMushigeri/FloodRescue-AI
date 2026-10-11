from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SenderRole(str, Enum):
    SURVIVOR = "survivor"
    RESPONDER = "responder"
    TEAM = "team"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    sender_role: SenderRole = SenderRole.SURVIVOR
    sender_name: str = Field(default="Survivor", max_length=100)
    message_content: str = Field(min_length=1, max_length=1000)


class Message(BaseModel):
    message_id: str
    incident_id: str
    sender_role: SenderRole
    sender_name: str
    message_content: str
    created_at: str
    delivery_status: str = "delivered"

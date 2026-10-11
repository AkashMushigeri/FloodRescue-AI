from __future__ import annotations
import re
from typing import List, Tuple
from backend.models.incident import (
    IncidentCreate,
    PriorityLevel,
    WaterLevel,
    AIAnalysisResult,
    AIProcessingStatus,
)


class DeterministicTriageEngine:
    """Safety-critical deterministic rule engine for flood distress triage.
    
    Guarantees deterministic safety flags regardless of AI model availability.
    """

    CRITICAL_KEYWORDS = [
        "drowning", "unconscious", "cannot breathe", "cardiac", "heart attack",
        "bleeding heavily", "severe injury", "submerged", "swept away", "roof collapsing",
        "trapped on roof", "water up to neck", "infant", "oxygen running out", "dialysis",
        "electric current in water", "choking", "diabetic shock"
    ]

    HIGH_KEYWORDS = [
        "rising fast", "waist deep", "chest deep", "pregnant", "elderly",
        "disabled", "wheelchair", "asthma", "broken leg", "fracture",
        "no drinking water", "trapped inside", "stairs flooded", "water entering"
    ]

    MISSING_INFO_CHECKS = [
        ("contact", ["phone", "call", "contact", "+91", "mobile", "cell"]),
        ("floor_or_exact_location", ["floor", "door", "apt", "flat", "street", "cross", "near", "opposite"]),
        ("water_depth", ["feet", "inches", "ankle", "knee", "waist", "chest", "neck", "floor"]),
    ]

    @classmethod
    def evaluate_priority(cls, incident: IncidentCreate) -> Tuple[PriorityLevel, List[str], List[str], List[str]]:
        reasons: List[str] = []
        dangers: List[str] = []
        missing_info: List[str] = []
        msg_lower = incident.distress_message.lower()

        # 1. Environmental Water Level Trigger
        if incident.water_level == WaterLevel.SUBMERGED_ROOF:
            reasons.append("Critical environmental hazard: Structure or roof submerged")
            dangers.append("Structure nearing full submergence")
        elif incident.water_level == WaterLevel.CHEST:
            reasons.append("High water level hazard: Chest-deep water reported")
            dangers.append("Severe mobility restriction and hypothermia risk")
        elif incident.water_level == WaterLevel.WAIST:
            reasons.append("Moderate water level hazard: Waist-deep water reported")
            dangers.append("Flooded ground level; stairs or egress obstructed")

        # 2. Medical Urgency Trigger
        if incident.has_injuries:
            if incident.injuries_description:
                reasons.append(f"Reported injury or medical emergency: {incident.injuries_description}")
                dangers.append(f"Medical trauma: {incident.injuries_description}")
            else:
                reasons.append("Reported injury or medical emergency (unspecified)")
                dangers.append("Active injury requiring emergency paramedic evaluation")

        # 3. Special Needs / Vulnerable Trapped Persons
        if incident.special_needs:
            vulnerable_str = ", ".join(incident.special_needs)
            reasons.append(f"Vulnerable occupants requiring specialized evacuation: {vulnerable_str}")
            dangers.append(f"Vulnerable individuals: {vulnerable_str}")

        # 4. Message Keyword Analysis
        for kw in cls.CRITICAL_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", msg_lower):
                reasons.append(f"Life-threatening indicator detected in message: '{kw}'")
                dangers.append(f"Life-threatening symptom: '{kw}'")

        for kw in cls.HIGH_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", msg_lower):
                dangers.append(f"High risk indicator: '{kw}'")

        # 5. Missing Information Audit
        if not incident.reporter_contact:
            missing_info.append("No direct return contact phone/radio provided")

        if incident.location_precision.value == "unverified" or len(incident.landmark_description.strip()) < 10:
            missing_info.append("Approximate or coarse location only; exact floor or street number unverified")

        if incident.water_level == WaterLevel.NONE and not any(kw in msg_lower for kw in ["water", "feet", "meter", "level"]):
            missing_info.append("Specific outdoor/indoor water depth unspecified in report")

        # 6. Synthesize Priority Level Deterministically
        priority = PriorityLevel.LOW
        if (
            incident.water_level in [WaterLevel.CHEST, WaterLevel.SUBMERGED_ROOF]
            or incident.has_injuries
            or any(kw in msg_lower for kw in cls.CRITICAL_KEYWORDS)
        ):
            priority = PriorityLevel.CRITICAL
        elif (
            incident.water_level == WaterLevel.WAIST
            or len(incident.special_needs) > 0
            or incident.people_reported >= 5
            or any(kw in msg_lower for kw in cls.HIGH_KEYWORDS)
        ):
            priority = PriorityLevel.HIGH
        elif incident.water_level in [WaterLevel.ANKLE, WaterLevel.NONE]:
            priority = PriorityLevel.MEDIUM

        if not reasons:
            reasons.append(f"Standard priority evaluation based on {incident.people_reported} people reported")

        return priority, reasons, list(set(dangers)), missing_info

    @classmethod
    def generate_fallback_analysis(cls, incident: IncidentCreate) -> AIAnalysisResult:
        priority, reasons, dangers, missing_info = cls.evaluate_priority(incident)
        
        # Build explainable recommendation
        next_steps = []
        if priority == PriorityLevel.CRITICAL:
            next_steps.append("Immediate human review: Dispatch swift water boat or paramedic unit")
            next_steps.append("Attempt survivor telephone/radio contact to confirm exact floor level")
        elif priority == PriorityLevel.HIGH:
            next_steps.append("Queue for high-water clearance vehicle or regional boat team")
            next_steps.append("Request survivor to move to highest accessible secure structure")
        else:
            next_steps.append("Log in operational queue for scheduled supply/welfare check")

        summary = (
            f"[{priority.value.upper()}] {incident.people_reported} reported at {incident.landmark_description}. "
            f"Water: {incident.water_level.value}. Injuries: {'Yes' if incident.has_injuries else 'No'}."
        )

        return AIAnalysisResult(
            confidence=0.75,
            immediate_dangers=dangers,
            missing_information=missing_info,
            recommended_next_steps=next_steps,
            duplicate_candidates=[],
            human_review_required=(priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]),
            suggested_priority=priority,
            priority_reasons=reasons,
            summary_for_dashboard=summary,
            processing_status=AIProcessingStatus.FALLBACK_RULES_ONLY,
            model_name="deterministic_safety_rules_v1",
        )

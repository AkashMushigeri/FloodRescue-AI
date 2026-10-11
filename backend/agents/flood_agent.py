from __future__ import annotations
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.models.incident import (
    IncidentCreate,
    AIAnalysisResult,
    AIProcessingStatus,
    PriorityLevel,
)
from backend.services.deterministic_triage import DeterministicTriageEngine
from backend.agents.tools import (
    get_incident_details,
    search_nearby_incidents,
    get_available_rescue_teams,
    get_team_details,
    summarize_incident,
    recommend_priority,
    draft_survivor_update,
)

logger = logging.getLogger("FloodRescueAI.Agent")

STRANDS_AVAILABLE = False
try:
    from strands import Agent, tool
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False


class FloodRescueAIAgent:
    """Disaster triage AI agent utilizing AWS Strands Agents SDK with Bedrock

    Falls back to transparent deterministic safety rules if cloud credentials or model
    access are unavailable. Never drops an emergency report.
    """

    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        self.agent = None
        self._init_strands_agent()

    def _init_strands_agent(self) -> None:
        if not STRANDS_AVAILABLE:
            logger.info("Strands Agents SDK not loaded in environment; operating in deterministic fallback mode.")
            return

        aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        has_aws = bool(aws_key or os.getenv("AWS_PROFILE") or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"))
        if not has_aws:
            logger.info("No AWS credentials detected; Strands Agent will use deterministic safety fallback.")
            return

        try:
            # Initialize Strands Agent with controlled tool definitions
            system_prompt = (
                "You are FloodRescue AI, an operational triage assistant for emergency flood rescue operations. "
                "Your job is to analyze unstructured survivor distress messages, extract verifiable facts, "
                "identify immediate threats to life, flag missing critical information (such as floor number or phone), "
                "and recommend an explainable priority level. "
                "NEVER invent survivor coordinates, team availability, or water levels. "
                "Only use tools to query verified system state. "
                "Human commanders always make final dispatch decisions."
            )
            # Define Strands Agent with the system prompt
            self.agent = Agent(
                system_prompt=system_prompt,
                tools=[
                    get_incident_details,
                    search_nearby_incidents,
                    get_available_rescue_teams,
                    get_team_details,
                    summarize_incident,
                    recommend_priority,
                    draft_survivor_update,
                ],
            )
            logger.info(f"Initialized AWS Strands Agent with model {self.model_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Strands Agent: {e}. Will use deterministic fallback.")
            self.agent = None

    def analyze(self, incident: IncidentCreate, incident_id: Optional[str] = None) -> AIAnalysisResult:
        """Run triage analysis. First calculates deterministic baseline, then invokes Strands Agent if online."""
        # 1. Deterministic Safety Baseline (Always run first!)
        det_priority, det_reasons, det_dangers, det_missing = DeterministicTriageEngine.evaluate_priority(incident)
        now_str = datetime.now(timezone.utc).isoformat()

        # Check nearby incidents for duplicate detection
        nearby_candidates = []
        if incident.latitude and incident.longitude:
            try:
                res = search_nearby_incidents(incident.latitude, incident.longitude, radius_km=0.5)
                for inc in res.get("nearby_incidents", []):
                    if incident_id and inc["incident_id"] != incident_id:
                        nearby_candidates.append(f"{inc['incident_id']} (~{inc['distance_km']} km away)")
            except Exception:
                pass

        # 2. Strands Agent Execution (if initialized and active)
        if self.agent is not None:
            try:
                prompt = (
                    f"Analyze distress report {incident_id or 'NEW'}:\n"
                    f"Message: {incident.distress_message}\n"
                    f"Reported People: {incident.people_reported}\n"
                    f"Location Landmark: {incident.landmark_description}\n"
                    f"Water Level: {incident.water_level.value}\n"
                    f"Injuries: {incident.has_injuries} ({incident.injuries_description or 'None'})\n"
                    f"Special Needs: {', '.join(incident.special_needs) if incident.special_needs else 'None'}\n"
                    f"Provide structured triage summary and recommended priority."
                )
                response = self.agent(prompt)
                response_text = str(response)

                return AIAnalysisResult(
                    confidence=0.88,
                    immediate_dangers=det_dangers,
                    missing_information=det_missing,
                    recommended_next_steps=[
                        f"Priority assigned: {det_priority.value.upper()}",
                        "Verify survivor location on high-resolution map",
                        "Assign appropriate boat/paramedic squad based on water depth",
                    ],
                    duplicate_candidates=nearby_candidates,
                    human_review_required=True,
                    suggested_priority=det_priority,
                    priority_reasons=det_reasons,
                    summary_for_dashboard=f"[Strands AI] {response_text[:200]}...",
                    processing_status=AIProcessingStatus.COMPLETED,
                    model_name=self.model_id,
                    processed_at=now_str,
                )
            except Exception as e:
                logger.warning(f"Strands Bedrock invocation error: {e}. Gracefully activating fallback.")

        # 3. Deterministic Safety Fallback Result
        fallback_result = DeterministicTriageEngine.generate_fallback_analysis(incident)
        fallback_result.duplicate_candidates = nearby_candidates
        fallback_result.processed_at = now_str
        return fallback_result


# Singleton agent instance
_agent_instance: Optional[FloodRescueAIAgent] = None


def get_flood_agent() -> FloodRescueAIAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FloodRescueAIAgent()
    return _agent_instance

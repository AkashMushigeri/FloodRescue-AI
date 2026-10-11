import os
import pytest
from fastapi.testclient import TestClient

# Ensure local test mode
os.environ["APP_MODE"] = "local"

from backend.api.app import app
from backend.models.incident import LocationType, WaterLevel, PriorityLevel, IncidentStatus, IncidentCreate
from backend.services.persistence import get_persistence_adapter
from backend.services.deterministic_triage import DeterministicTriageEngine
from backend.agents.flood_agent import FloodRescueAIAgent
from backend.agents.tools import (
    get_incident_details,
    search_nearby_incidents,
    get_available_rescue_teams,
    get_team_details,
    summarize_incident,
    recommend_priority,
    draft_survivor_update,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    adapter = get_persistence_adapter()
    # Reset local DB between test runs
    adapter.seed_simulated_data()
    yield


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FloodRescue AI"
    assert data["app_mode"] == "local"
    assert data["is_simulated_mode"] is True


def test_submit_valid_sos():
    payload = {
        "reporter_name": "Test Survivor",
        "reporter_contact": "+91 99999 88888",
        "people_reported": 3,
        "distress_message": "Water rising rapidly up to knees. Need boat assistance.",
        "location_type": "landmark_only",
        "landmark_description": "Near Metro Pillar 45, Anna Salai",
        "water_level": "waist",
        "has_injuries": False,
        "special_needs": ["elderly"],
        "idempotency_key": "test-key-001",
        "is_simulated": True,
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"].startswith("INC-2026-")
    assert data["people_reported"] == 3
    assert data["status"] == "reported"
    assert data["suggested_priority"] in ["high", "critical"]
    assert "ai_analysis" in data
    assert data["ai_analysis"]["processing_status"] in ["completed", "fallback_rules_only"]


def test_reject_invalid_people_count():
    payload = {
        "reporter_name": "Invalid Count",
        "people_reported": 0,  # Invalid! Must be >= 1
        "distress_message": "Testing invalid count",
        "landmark_description": "Some landmark",
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 422


def test_landmark_without_gps():
    payload = {
        "reporter_name": "No GPS User",
        "people_reported": 2,
        "distress_message": "Trapped on terrace, road flooded completely",
        "location_type": "landmark_only",
        "landmark_description": "Green Apartments, 3rd Floor, Lake View Road",
        "water_level": "ankle",
        "has_injuries": False,
        "is_simulated": True,
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["location_precision"] == "approximate"
    assert "Green Apartments" in data["landmark_description"]


def test_medical_emergency_triage_priority():
    payload = {
        "reporter_name": "Critical Medical Report",
        "people_reported": 1,
        "distress_message": "Unconscious person bleeding heavily after wall collapse in flood waters.",
        "location_type": "landmark_only",
        "landmark_description": "Sector 4 Primary Health Center lane",
        "water_level": "chest",
        "has_injuries": True,
        "injuries_description": "Head trauma, unconscious, heavy bleeding",
        "is_simulated": True,
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["suggested_priority"] == "critical"
    reasons_text = " ".join(data["priority_reasons"]).lower()
    assert "chest" in reasons_text or "injury" in reasons_text or "bleeding" in reasons_text


def test_idempotency_prevents_duplicate_submission():
    payload = {
        "reporter_name": "Duplicate Clicker",
        "people_reported": 4,
        "distress_message": "Water entering first floor",
        "landmark_description": "Plot 12, Gandhi Nagar",
        "idempotency_key": "unique-uuid-idemp-12345",
        "is_simulated": True,
    }
    # First submission
    r1 = client.post("/incidents", json=payload)
    assert r1.status_code == 201
    id1 = r1.json()["incident_id"]

    # Repeated submission with identical key
    r2 = client.post("/incidents", json=payload)
    assert r2.status_code in [200, 201]
    id2 = r2.json()["incident_id"]
    assert id1 == id2, "Idempotency key must return the exact same incident record"


def test_incident_workflow_lifecycle():
    # 1. Create incident
    payload = {
        "reporter_name": "Workflow Survivor",
        "people_reported": 2,
        "distress_message": "Stuck in building",
        "landmark_description": "Tower B, Floor 2",
        "is_simulated": True,
    }
    res = client.post("/incidents", json=payload)
    inc_id = res.json()["incident_id"]
    assert res.json()["status"] == "reported"

    # Guard check: Cannot directly resolve without acknowledging/assigning
    bad_resolve = client.post(f"/incidents/{inc_id}/resolve")
    assert bad_resolve.status_code == 400

    # 2. Operations Acknowledges
    ack_res = client.post(f"/incidents/{inc_id}/acknowledge?dispatcher_id=DISPATCH-ALPHA")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"
    assert ack_res.json()["acknowledged_by"] == "DISPATCH-ALPHA"

    # 3. Assign team
    assign_payload = {
        "team_id": "TEAM-SWIFT-01",
        "dispatcher_id": "DISPATCH-ALPHA",
        "dispatch_notes": "Deploy boat squad to Tower B",
    }
    assign_res = client.post(f"/incidents/{inc_id}/assign", json=assign_payload)
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"
    assert assign_res.json()["assigned_team_id"] == "TEAM-SWIFT-01"

    # Check team status became DISPATCHED
    team_res = client.get("/teams/TEAM-SWIFT-01")
    assert team_res.status_code == 200
    assert team_res.json()["status"] == "dispatched"
    assert inc_id in team_res.json()["assigned_incidents"]

    # Guard check: Cannot assign team to resolved incident
    # First resolve:
    resolve_res = client.post(f"/incidents/{inc_id}/resolve?resolved_by=DISPATCH-ALPHA")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

    # Now attempt assign to resolved:
    bad_assign = client.post(f"/incidents/{inc_id}/assign", json=assign_payload)
    assert bad_assign.status_code == 400


def test_dashboard_metrics_distinguish_people_from_incidents():
    res = client.get("/incidents")
    assert res.status_code == 200
    data = res.json()
    metrics = data["metrics"]
    assert "people_reported" in metrics
    assert "known_reported_incidents" in metrics
    # People count is the sum of reported people, strictly >= incident count
    assert metrics["people_reported"] >= metrics["known_reported_incidents"]


def test_controlled_tools():
    # 1. Available teams tool
    teams = get_available_rescue_teams()
    assert "available_team_count" in teams
    assert isinstance(teams["teams"], list)

    # 2. Survivor update drafting tool
    draft = draft_survivor_update("INC-2026-SIM-01", "assigned")
    assert "drafted_message" in draft
    assert "INC-2026-SIM-01" in draft["drafted_message"]

    # 3. Nearby incidents tool
    nearby = search_nearby_incidents(13.0334, 80.2182, radius_km=5.0)
    assert "nearby_incidents" in nearby
    assert nearby["count"] >= 1

    # 4. Incident summary tool
    summary = summarize_incident("INC-2026-SIM-01")
    assert "executive_summary" in summary
    assert "INC-2026-SIM-01" in summary["incident_id"]

    # 5. Coordinate validation guard in search_nearby_incidents
    invalid_search = search_nearby_incidents(999.0, 999.0)
    assert "error" in invalid_search


def test_search_filters_and_pagination():
    res = client.get("/incidents?limit=2&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) <= 2

    # Filter by priority
    res_crit = client.get("/incidents?priority=critical")
    assert res_crit.status_code == 200
    for item in res_crit.json()["items"]:
        assert item["suggested_priority"] == "critical"


def test_ai_agent_triage_fallback_resilience():
    agent = FloodRescueAIAgent()
    inc = IncidentCreate(
        reporter_name="Trapped Resident",
        people_reported=5,
        distress_message="Elderly diabetic resident on dialysis trapped on roof as water reaches chest level.",
        landmark_description="Plot 5, Lakeview Road",
        water_level=WaterLevel.CHEST,
        has_injuries=True,
        injuries_description="Missed dialysis treatment, breathless",
        special_needs=["elderly", "medical_devices"],
        is_simulated=True,
    )
    analysis = agent.analyze(inc)
    assert analysis.suggested_priority == PriorityLevel.CRITICAL
    assert len(analysis.priority_reasons) > 0
    assert analysis.human_review_required is True
    assert analysis.processing_status in ["completed", "fallback_rules_only"]


def test_incident_discussion_thread():
    # Post a message to an incident
    post_res = client.post(
        "/incidents/INC-2026-SIM-01/messages",
        json={
            "sender_role": "responder",
            "sender_name": "Operations Commander",
            "message_content": "Boat squad deployed to your coordinates.",
        },
    )
    assert post_res.status_code == 201

    # Retrieve messages
    get_res = client.get("/incidents/INC-2026-SIM-01/messages")
    assert get_res.status_code == 200
    msgs = get_res.json()
    assert any("Boat squad deployed" in m["message_content"] for m in msgs)


def test_team_status_updates():
    patch_res = client.patch(
        "/teams/TEAM-SWIFT-01/status",
        json={"status": "on_scene", "responder_id": "FIELD-LEAD-01"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "on_scene"

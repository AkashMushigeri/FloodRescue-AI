from __future__ import annotations
import math
from typing import Any, Dict, List, Optional
from backend.services.persistence import get_persistence_adapter
from backend.models.incident import PriorityLevel, IncidentStatus
from backend.models.team import TeamStatus


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in km."""
    r = 6371.0  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def get_incident_details(incident_id: str) -> Dict[str, Any]:
    """Retrieve verified stored incident record by its unique ID.
    
    Returns structured incident details or an error message if not found.
    Does not invent data.
    """
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        return {"error": f"Incident '{incident_id}' not found in registry."}
    return incident.model_dump()


def search_nearby_incidents(latitude: float, longitude: float, radius_km: float = 3.0) -> Dict[str, Any]:
    """Search for already reported incidents within a given radius in kilometers.
    
    Used to identify potential duplicate reports and assess local cluster density.
    Only considers incidents with valid coordinates.
    """
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        return {"error": "Invalid coordinates supplied to search_nearby_incidents."}
    
    if radius_km <= 0 or radius_km > 50:
        return {"error": "Radius must be between 0.1 and 50 km."}

    adapter = get_persistence_adapter()
    incidents, _ = adapter.list_incidents(limit=200)
    
    nearby: List[Dict[str, Any]] = []
    for inc in incidents:
        if inc.latitude is not None and inc.longitude is not None:
            dist = haversine_km(latitude, longitude, inc.latitude, inc.longitude)
            if dist <= radius_km:
                nearby.append({
                    "incident_id": inc.incident_id,
                    "distance_km": round(dist, 2),
                    "people_reported": inc.people_reported,
                    "landmark_description": inc.landmark_description,
                    "status": inc.status.value,
                    "priority": inc.suggested_priority.value,
                    "has_injuries": inc.has_injuries,
                    "is_simulated": inc.is_simulated,
                })

    nearby.sort(key=lambda x: x["distance_km"])
    return {
        "query_center": {"latitude": latitude, "longitude": longitude, "radius_km": radius_km},
        "count": len(nearby),
        "nearby_incidents": nearby,
    }


def get_available_rescue_teams() -> Dict[str, Any]:
    """Retrieve all authorized rescue teams that are currently available for dispatch."""
    adapter = get_persistence_adapter()
    teams = adapter.list_teams()
    available = [t.model_dump() for t in teams if t.status == TeamStatus.AVAILABLE]
    return {
        "available_team_count": len(available),
        "teams": available,
    }


def get_team_details(team_id: str) -> Dict[str, Any]:
    """Retrieve specific team equipment, personnel count, and operational status."""
    adapter = get_persistence_adapter()
    team = adapter.get_team(team_id)
    if not team:
        return {"error": f"Rescue team '{team_id}' not found."}
    return team.model_dump()


def summarize_incident(incident_id: str) -> Dict[str, Any]:
    """Prepare a clear, structured operational summary of an incident for responders."""
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        return {"error": f"Incident '{incident_id}' not found."}

    special = ", ".join(incident.special_needs) if incident.special_needs else "None declared"
    loc = f"{incident.landmark_description} (Precision: {incident.location_precision.value})"
    if incident.latitude and incident.longitude:
        loc += f" [{incident.latitude:.4f}, {incident.longitude:.4f}]"

    summary_text = (
        f"Incident {incident.incident_id}: {incident.people_reported} people reported. "
        f"Location: {loc}. Water: {incident.water_level.value}. "
        f"Injuries: {'Yes - ' + str(incident.injuries_description) if incident.has_injuries else 'None reported'}. "
        f"Special needs: {special}."
    )

    return {
        "incident_id": incident.incident_id,
        "executive_summary": summary_text,
        "distress_message": incident.distress_message,
        "priority": incident.suggested_priority.value,
        "priority_reasons": incident.priority_reasons,
        "status": incident.status.value,
        "is_simulated": incident.is_simulated,
    }


def recommend_priority(incident_id: str) -> Dict[str, Any]:
    """Generate an explainable priority recommendation based on verified parameters."""
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        return {"error": f"Incident '{incident_id}' not found."}

    # Retrieve nearby incidents to check clustering or duplicates
    duplicates = []
    if incident.latitude and incident.longitude:
        nearby = search_nearby_incidents(incident.latitude, incident.longitude, radius_km=0.3)
        duplicates = [
            n["incident_id"]
            for n in nearby.get("nearby_incidents", [])
            if n["incident_id"] != incident.incident_id
        ]

    return {
        "incident_id": incident.incident_id,
        "suggested_priority": incident.suggested_priority.value,
        "priority_reasons": incident.priority_reasons,
        "potential_duplicate_incident_ids": duplicates,
        "human_review_required": True,
        "caveat": "Recommendations assist triage; authorized human incident commander must make dispatch decisions.",
    }


def draft_survivor_update(incident_id: str, new_status: str) -> Dict[str, Any]:
    """Draft an honest, empathetic, and safe message update for the survivor.
    
    Never promises rescue team arrival time unless confirmed by an authorized responder.
    """
    adapter = get_persistence_adapter()
    incident = adapter.get_incident(incident_id)
    if not incident:
        return {"error": f"Incident '{incident_id}' not found."}

    templates = {
        IncidentStatus.REPORTED.value: (
            "Your distress report has been securely registered in the FloodRescue system (Reference: {ref}). "
            "Our emergency operations center has received your report and safety triage is underway. "
            "Please move to the highest accessible safe floor if water is rising."
        ),
        IncidentStatus.ACKNOWLEDGED.value: (
            "Your report {ref} has been reviewed and acknowledged by the Emergency Coordination Center. "
            "Responders are evaluating water conditions and team availability in your sector. "
            "Keep your phone in battery saver mode if possible."
        ),
        IncidentStatus.ASSIGNED.value: (
            "Rescue Team ({team}) has been assigned to your incident {ref}. "
            "The team is preparing gear and coordinating their route. "
            "Please remain in a safe, visible position with bright cloth or a flashlight."
        ),
        IncidentStatus.IN_PROGRESS.value: (
            "Rescue Team ({team}) is actively deployed towards your reported area for incident {ref}. "
            "Please listen for boat engines or responder whistles."
        ),
        IncidentStatus.RESOLVED.value: (
            "Incident {ref} has been marked resolved. If you or anyone nearby still require emergency assistance, "
            "please submit a new distress signal immediately."
        ),
    }

    team_label = incident.assigned_team_id or "Authorized Response Team"
    text_template = templates.get(new_status, "Status update for incident {ref}: Current status is {status}.")
    drafted_text = text_template.format(ref=incident.incident_id, team=team_label, status=new_status)

    return {
        "incident_id": incident.incident_id,
        "target_status": new_status,
        "drafted_message": drafted_text,
        "safety_reminder": "Keep safe distance from submerged electrical conduits and open drains.",
    }

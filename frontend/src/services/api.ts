import type {
  Incident,
  IncidentCreatePayload,
  IncidentListResponse,
  RescueTeam,
  Message,
  HealthResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async createIncident(payload: IncidentCreatePayload): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(payload.idempotency_key ? { 'X-Idempotency-Key': payload.idempotency_key } : {}),
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<Incident>(res);
  },

  async listIncidents(params?: {
    status?: string;
    priority?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<IncidentListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.priority) query.set('priority', params.priority);
    if (params?.search) query.set('search', params.search);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    const res = await fetch(`${API_BASE}/incidents?${query.toString()}`);
    return handleResponse<IncidentListResponse>(res);
  },

  async getIncident(incidentId: string): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
    return handleResponse<Incident>(res);
  },

  async acknowledgeIncident(incidentId: string, dispatcherId: string = 'DISPATCHER-01'): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/acknowledge?dispatcher_id=${encodeURIComponent(dispatcherId)}`, {
      method: 'POST',
    });
    return handleResponse<Incident>(res);
  },

  async assignTeam(incidentId: string, teamId: string, dispatcherId: string = 'DISPATCHER-01', notes?: string): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId, dispatcher_id: dispatcherId, dispatch_notes: notes }),
    });
    return handleResponse<Incident>(res);
  },

  async resolveIncident(incidentId: string, resolvedBy: string = 'DISPATCHER-01'): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/resolve?resolved_by=${encodeURIComponent(resolvedBy)}`, {
      method: 'POST',
    });
    return handleResponse<Incident>(res);
  },

  async triggerAIAnalysis(incidentId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/analyze`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async listTeams(): Promise<RescueTeam[]> {
    const res = await fetch(`${API_BASE}/teams`);
    return handleResponse<RescueTeam[]>(res);
  },

  async getTeam(teamId: string): Promise<RescueTeam> {
    const res = await fetch(`${API_BASE}/teams/${teamId}`);
    return handleResponse<RescueTeam>(res);
  },

  async updateTeamStatus(teamId: string, status: string, responderId: string = 'TEAM-LEAD'): Promise<RescueTeam> {
    const res = await fetch(`${API_BASE}/teams/${teamId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, responder_id: responderId }),
    });
    return handleResponse<RescueTeam>(res);
  },

  async getMessages(incidentId: string): Promise<Message[]> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/messages`);
    return handleResponse<Message[]>(res);
  },

  async postMessage(incidentId: string, content: string, senderRole: string = 'survivor', senderName: string = 'Survivor'): Promise<Message> {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message_content: content,
        sender_role: senderRole,
        sender_name: senderName,
      }),
    });
    return handleResponse<Message>(res);
  },

  async seedSimulatedData(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/seed-simulated-data`, {
      method: 'POST',
    });
    return handleResponse<{ message: string }>(res);
  },
};

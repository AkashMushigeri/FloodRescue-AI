export type LocationType = 'gps' | 'manual_pin' | 'landmark_only';
export type LocationPrecision = 'exact' | 'approximate' | 'unverified';
export type WaterLevel = 'none' | 'ankle' | 'waist' | 'chest' | 'submerged_roof';
export type IncidentStatus = 'reported' | 'acknowledged' | 'assigned' | 'in_progress' | 'resolved' | 'cancelled';
export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low';
export type TeamStatus = 'available' | 'dispatched' | 'on_scene' | 'returning' | 'offline';
export type SenderRole = 'survivor' | 'responder' | 'team' | 'system';

export interface AIAnalysisResult {
  confidence: number;
  immediate_dangers: string[];
  missing_information: string[];
  recommended_next_steps: string[];
  duplicate_candidates: string[];
  human_review_required: boolean;
  suggested_priority: PriorityLevel;
  priority_reasons: string[];
  summary_for_dashboard: string;
  processing_status: 'pending' | 'completed' | 'fallback_rules_only' | 'failed';
  model_name?: string;
  processed_at?: string;
}

export interface Incident {
  incident_id: string;
  created_at: string;
  updated_at: string;
  reporter_name: string;
  reporter_contact?: string;
  people_reported: number;
  distress_message: string;
  location_type: LocationType;
  latitude?: number;
  longitude?: number;
  landmark_description: string;
  location_precision: LocationPrecision;
  water_level: WaterLevel;
  has_injuries: boolean;
  injuries_description?: string;
  special_needs: string[];
  status: IncidentStatus;
  suggested_priority: PriorityLevel;
  priority_reasons: string[];
  assigned_team_id?: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  ai_analysis?: AIAnalysisResult;
  idempotency_key?: string;
  is_simulated: boolean;
  data_source: string;
}

export interface IncidentCreatePayload {
  reporter_name?: string;
  reporter_contact?: string;
  people_reported: number;
  distress_message: string;
  location_type: LocationType;
  latitude?: number;
  longitude?: number;
  landmark_description: string;
  location_precision: LocationPrecision;
  water_level: WaterLevel;
  has_injuries: boolean;
  injuries_description?: string;
  special_needs: string[];
  idempotency_key?: string;
  is_simulated?: boolean;
}

export interface RescueTeam {
  team_id: string;
  team_name: string;
  personnel_count: number;
  status: TeamStatus;
  capabilities: string[];
  current_latitude?: number;
  current_longitude?: number;
  current_location_name: string;
  assigned_incidents: string[];
  last_location_update: string;
  contact_channel: string;
  is_simulated: boolean;
}

export interface Message {
  message_id: string;
  incident_id: string;
  sender_role: SenderRole;
  sender_name: string;
  message_content: string;
  created_at: string;
  delivery_status: string;
}

export interface OperationalMetrics {
  people_reported: number;
  known_reported_incidents: number;
  urgent_review_required: number;
  location_verification_needed: number;
  assigned_count: number;
  resolved_count: number;
}

export interface IncidentListResponse {
  items: Incident[];
  total: number;
  metrics: OperationalMetrics;
}

export interface HealthResponse {
  status: string;
  service: string;
  app_mode: 'local' | 'aws';
  timestamp: string;
  persistence_type: string;
  is_simulated_mode: boolean;
}

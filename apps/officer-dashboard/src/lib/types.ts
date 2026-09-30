export type Provenance = {
  source: string;
  reference_timestamp?: string | null;
  is_sample: boolean;
  is_synthetic: boolean;
  mode: "live" | "demo";
  note?: string | null;
};

export type Block = { block: string; avg_farm_health: number; water_stress_index: number; disease_alerts: number };

export type District = {
  district_id: string;
  district: string;
  lat: number;
  lon: number;
  farmers_represented: number;
  fields_represented: number;
  crop_distribution_pct: Record<string, number>;
  avg_farm_health: number;
  water_stress_index: number;
  weather_risk: "low" | "medium" | "high";
  weather_risk_reason: string;
  disease_alerts: number;
  top_issues: string[];
  advisories_issued_7d: number;
  reference_date: string;
};

export type PlatformActivity = {
  registered_fields: number;
  registered_farmers: number;
  advisories_generated: number;
  diagnoses: number;
  crop_recommendations: number;
  pending_reviews: number;
  recent_diagnoses: { diagnosis_id: string; district: string | null; crop: string; potential_condition: string; severity: string; confidence: number; created_at: string }[];
};

export type Totals = {
  farmers_represented: number;
  fields_represented: number;
  avg_farm_health: number;
  avg_water_stress_index: number;
  disease_alerts: number;
  advisories_issued_7d: number;
  high_weather_risk_districts: number;
  active_crops: number;
};

export type StateAnalytics = {
  state_id: string;
  state_name: string;
  primary_crop: string;
  provenance: Provenance;
  totals: Totals;
  crop_distribution_pct: Record<string, number>;
  districts: District[];
  hotspots: { district_id: string; district: string; disease_alerts: number; top_issues: string[]; weather_risk: string }[];
  platform_activity: PlatformActivity;
};

export type Overview = {
  states: ({ state_id: string; state_name: string; primary_crop: string; lat: number; lon: number } & Totals)[];
  demo_mode: boolean;
  platform_activity: PlatformActivity;
};

export type DistrictRisks = District & {
  state_id: string;
  blocks: Block[];
  risks: { type: string; level: string; detail: string }[];
  provenance: Provenance;
  platform_activity: PlatformActivity;
};

export type ReviewItem = {
  kind: "advisories" | "diagnoses" | "crop_recommendations";
  id: string;
  field_id: string | null;
  state: string | null;
  district: string | null;
  title: string | null;
  severity: string | null;
  requires_review_reason: string;
  model_name: string;
  prompt_version: string;
  demo_mode: boolean;
  created_at: string;
  review: { status: string; reviewer?: string | null; note?: string | null };
  detail: Record<string, unknown>;
};

export type AdapterDemo = {
  state_id: string;
  state_name: string;
  adapter_version: string;
  source_system: string;
  source_meta: Record<string, unknown>;
  examples: { entity: string; raw: Record<string, unknown>; mapping: Record<string, unknown>; canonical: Record<string, unknown> }[];
};

export type Integration = { key: string; label: string; mode: "live" | "demo" | null; env: string; detail: string };

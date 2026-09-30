export type Lang = "en" | "hi" | "te";

export type Provenance = {
  source: string;
  source_url?: string | null;
  reference_timestamp?: string | null;
  retrieved_at: string;
  is_sample: boolean;
  is_synthetic: boolean;
  mode: "live" | "demo";
  note?: string | null;
};

export type Polygon = { type: "Polygon"; coordinates: number[][][] };

export type Farmer = {
  farmer_id: string;
  name: string;
  preferred_language: Lang;
  state: string;
  district: string;
  block?: string | null;
  village?: string | null;
  is_sample: boolean;
  source_system: string;
};

export type Field = {
  field_id: string;
  farmer_id: string;
  name?: string | null;
  state: string;
  district: string;
  block?: string | null;
  village?: string | null;
  place_label?: string | null;
  geometry: Polygon;
  centroid: { lat: number; lon: number };
  area_acres: number;
  irrigation: string;
  farming_practice: string;
  crop: { crop_name: string; variety?: string | null; season?: string | null; sowing_date?: string | null; growth_stage?: string | null };
  is_sample: boolean;
  source_system: string;
};

export type StateConfig = {
  state_id: string;
  state_name: string;
  primary_crop: string;
  default_language: Lang;
  supported_crops: string[];
  source_system: string;
  districts: { id: string; name: string; lat: number; lon: number }[];
};

export type Crop = { crop_id: string; names: Record<Lang, string>; family: string; seasons: string[] };

export type DailyWeather = {
  date: string;
  tmax_c: number | null;
  tmin_c: number | null;
  rain_mm: number | null;
  rain_probability_pct: number | null;
  is_forecast: boolean;
};

export type HealthFactor = {
  key: "vegetation" | "soil" | "weather" | "water" | "crop_condition";
  label: string;
  weight: number;
  score: number | null;
  status: "good" | "moderate" | "poor" | "missing";
  drivers: string[];
};

export type FarmHealth = {
  score: number;
  band: "Good" | "Moderate" | "Poor";
  factors: HealthFactor[];
  weights: Record<string, number>;
  effective_weights: Record<string, number>;
  missing_factors: string[];
  method: string;
};

export type DataSource = {
  category: string;
  source: string;
  mode: "live" | "demo";
  is_sample: boolean;
  is_synthetic: boolean;
  reference_timestamp: string | null;
  note?: string | null;
};

export type Intelligence = {
  farmer: Farmer;
  field: Field;
  crop: { crop_id: string; name: string; names: Record<Lang, string>; variety?: string | null; sowing_date?: string | null };
  current_stage: { stage: string; days_after_sowing: number | null; expected_ndvi: number | null };
  as_of_date: string;
  scenario_note: string | null;
  weather: {
    temperature_c: number | null;
    humidity_pct: number | null;
    wind_kmh: number | null;
    soil_moisture_m3_m3: number | null;
    rain_past_14d_mm: number | null;
    rain_next_3d_mm: number | null;
    rain_next_7d_mm: number | null;
    tmax_next_7d_c: number | null;
    daily: DailyWeather[];
    alerts: { code: string; severity: string; message: string }[];
    provenance: Provenance;
  };
  soil: null | {
    ph: number | null;
    organic_carbon_pct: number | null;
    nitrogen_kg_ha: number | null;
    phosphorus_kg_ha: number | null;
    potassium_kg_ha: number | null;
    clay_pct: number | null;
    sand_pct: number | null;
    silt_pct: number | null;
    measurement_date: string | null;
    provenance: Provenance;
    texture_provenance: Provenance | null;
  };
  satellite: {
    series: { date: string; ndvi: number; ndmi: number | null }[];
    latest_ndvi: number | null;
    ndvi_change_30d: number | null;
    vegetation_health: string;
    observation_date: string | null;
    thumbnail_url: string | null;
    provenance: Provenance;
  };
  health: FarmHealth;
  data_sources: DataSource[];
  demo_mode: boolean;
};

export type AIMeta = {
  model_name: string;
  model_version: string;
  prompt_version: string;
  generated_at: string;
  mode: "live" | "demo";
  fallback_reason?: string | null;
};

export type Review = { status: "pending_officer_review" | "approved" | "rejected"; reviewer?: string | null; note?: string | null };

export type AdvisoryContent = {
  summary: string;
  risk_level: "low" | "medium" | "high";
  time_sensitivity: string;
  observations: { category: string; fact: string; source: string }[];
  interpretations: { statement: string; based_on: string[]; uncertainty: string }[];
  recommendations: { action: string; priority: string; reason: string; timeframe: string }[];
  regenerative_practice: { action: string; reason: string; evidence: string[] };
  missing_information: string[];
  data_freshness_notes: string[];
  confidence: number;
  requires_human_review: boolean;
};

export type Advisory = {
  advisory_id: string;
  field_id: string;
  content: AdvisoryContent;
  localized: Record<string, { language: Lang; content: AdvisoryContent; method: string }>;
  ai: AIMeta;
  review: Review;
  demo_mode: boolean;
  generated_at: string;
};

export type CropOption = {
  crop_id: string;
  names: Record<Lang, string>;
  score: number;
  suitability: "High" | "Moderate" | "Low";
  rule_suitability: string;
  breakdown: Record<string, number>;
  reasons: string[];
  risks: string[];
  regenerative_role: string;
};

export type CropRecommendation = {
  recommendation_id: string;
  summary: string;
  season: string;
  options: CropOption[];
  rotation_plan: string;
  missing_information: string[];
  ai: AIMeta;
  review: Review;
  demo_mode: boolean;
};

export type Diagnosis = {
  diagnosis_id: string;
  crop: string;
  image_url: string;
  potential_condition: string;
  confidence: number;
  severity: string;
  disclaimer: string;
  result: {
    image_usable: boolean;
    image_issue: string;
    plant_part: string;
    potential_conditions: { name: string; likelihood: number; visible_evidence: string[] }[];
    visible_symptoms: string[];
    severity: string;
    confidence: number;
    recommended_next_actions: string[];
    requires_expert_review: boolean;
    explanation: string;
  };
  ai: AIMeta;
  review: Review;
  demo_mode: boolean;
};

export type AskAnswer = {
  answer: string;
  grounded_on: string[];
  follow_up_suggestion: string;
  requires_expert_review: boolean;
  intent: string;
  ai: AIMeta;
  demo_mode: boolean;
};

export type Integration = { key: string; label: string; mode: "live" | "demo" | null; env: string; detail: string };
export type SystemStatus = { integrations: Integration[]; demo_mode: boolean; gemini_model: string };

export type SupportPlace = {
  name: string;
  address: string;
  kind: string;
  lat: number;
  lon: number;
  straight_km: number;
  distance_km?: number;
  duration_min?: number;
  maps_url: string;
};
export type NearbySupport = { field_id: string; places: SupportPlace[]; mode: "live" | "demo" | "error"; source?: string; note?: string };
export type GeocodeResult = { label: string; lat: number; lon: number; village?: string | null; district?: string | null; state?: string | null };

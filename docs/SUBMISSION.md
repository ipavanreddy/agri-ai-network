# Agri AI Network: submission pack

Track 4 · Build with AI (Google) · Repository: https://github.com/ipavanreddy/agri-ai-network

## Product description (2-3 lines)

Agri AI Network gives a smallholder farmer one AI advisor for their own field: live weather, Soil Health Card data
and satellite vegetation become an explainable Farm Health score, and Gemini turns it into a grounded advisory,
crop options and a photo-based Crop Doctor, in English, Hindi or Telugu, by voice or text. A shared canonical data
model with declarative state adapters lets any state plug in its own records and gives agriculture officers a
district-level risk view with human review of every AI output.

## Live URLs

| | URL |
|---|---|
| Farmer app | https://agri-ai-network-farmer-web-847963771142.asia-south1.run.app |
| Agriculture Officer dashboard | https://agri-ai-network-officer-dashboard-847963771142.asia-south1.run.app |
| API + OpenAPI docs | https://agri-ai-network-api-847963771142.asia-south1.run.app/docs |

Deployment is one command: `infrastructure/cloud-run/deploy.sh` (see [infrastructure/cloud-run/README.md](../infrastructure/cloud-run/README.md)).

## Demo video script (4 min 45 s)

Follows PRD §44 as one continuous story. Record at 1440×900, browser zoom 110 %. Before recording: open the three
URLs once (Cloud Run cold start), open `/api/system/status` to confirm Gemini / Speech / Translation / Maps /
BigQuery / Storage show `live`, and keep a Telugu-capable microphone setting ready. If the network is unreliable, tick
*Use sample scenario data (offline demo)*: the story stays identical and is labelled as sample.

| Time | Scene (screen) | Action | Voice-over (key line) |
|---|---|---|---|
| 0:00-0:15 | Title slide / farmer app header | Show the header: language buttons, *"N integrations live"* badge and the *Demo mode* panel expanded for one second | "Agri AI Network: one AI advisor for a smallholder's own field, built on Google Cloud and Gemini." |
| 0:15-0:35 | **1. My field** | Click *Lakshmi Devi · Groundnut · AP*. The map zooms to her 2.4-acre field in Anantapur. Briefly click *Register a new field*, type "Kalyandurg" in *Find village / town* to show the Maps search, then cancel | "Meet Lakshmi, a smallholder growing groundnut on 2.4 acres in Anantapur. Any farmer can find their village and tap the corners of their field." |
| 0:35-1:10 | **2. Farm intelligence** | Scroll through Weather (Open-Meteo, *Live*), Soil (Soil Health Card via the AP adapter + SoilGrids), Satellite NDVI chart, then the **Farm Health** score and per-factor breakdown | "Weather, soil and satellite signals, each with its source and freshness, combine into an explainable Farm Health score: vegetation 30 %, soil 25 %, weather 20 %, water 15 %, crop condition 10 %. Missing data is never invented." |
| 1:10-1:50 | **3. Today's advisory** | Click *Generate advisory*. Point at the *Gemini · gemini-2.5-flash* badge, then *Observed data* → *AI interpretation* → *Recommended actions*, *Risk*, the *Regenerative practice* and *Missing information*. Scroll to **4. Crop recommendations**, click *Recommend crops*: ≥ 3 crops with suitability and rotation plan | "Gemini on Vertex AI receives only structured field context and must answer in a validated schema: what we observed, what it means, what to do, plus one regenerative practice for this field. Every record stores model and prompt version and goes to an officer for review." |
| 1:50-2:30 | **5. Crop Doctor** | Click *Use sample leaf photo* (or upload a real groundnut leaf photo), then *Analyse photo*. Show *Potential condition*, *Confidence*, *Visible symptoms*, *Recommended next steps*, the disclaimer, and **Nearest agriculture support** with road distance and drive time | "Gemini multimodal gives a preliminary assessment with confidence and visible symptoms, never a certified diagnosis. Google Maps finds the nearest agriculture office or KVK and how long the drive is. Farm Health now includes crop condition." |
| 2:30-3:00 | Language + **6. Ask by voice** | Click *తెలుగు*: the same advisory is re-presented in Telugu (Cloud Translation) without re-analysis. Tap *Speak*, ask "వర్షం ఎప్పుడు వస్తుంది? నీటి తడి ఇవ్వాలా?" (When will it rain? Should I irrigate?). The transcript appears and the answer is spoken | "Lakshmi switches to Telugu and simply asks. Cloud Speech-to-Text, a Gemini answer grounded in her field's forecast and soil moisture, and Cloud Text-to-Speech reply in her language." |
| 3:00-3:40 | **Officer dashboard** → *Regional risks* | Open the officer URL. India → click Andhra Pradesh → Anantapur → blocks. Show *Crop distribution*, *Disease / stress hotspots*, *Weather risk* / *Water stress* columns and *Live platform activity*. Open *Review queue*, approve Lakshmi's advisory with a note | "The agriculture officer sees the same network from above: state, district and block risk served from BigQuery, disease hotspots, and every AI output waiting for human approval. Approved, and Lakshmi's app shows it." |
| 3:40-4:20 | *Interoperability* tab | Switch AP → Maharashtra → Punjab. Show raw state record (Telugu/Marathi/Punjabi field names, kanal/ha units, local crop codes like *kanak*), the adapter mapping, and the identical canonical record | "Every state keeps its own systems. A declarative adapter maps AP e-Crop, Maharashtra MahaDBT and Punjab land records into one canonical schema, so the same AI services run unchanged. Onboarding a state is a config file and a data export." |
| 4:20-4:45 | Architecture slide (README diagram) | Show the Cloud Run services, Gemini on Vertex AI, Speech, Translation, Maps, BigQuery, Cloud Storage, Earth Engine | "One field, one district, one state, many states: a national agriculture intelligence network on Google Cloud, and the same adapters carry it to BRICS partners." |

## Definition of Done (PRD §56)

Legend: ✅ done · ⚠️ done with a caveat · ❌ not done.

### Farmer experience
| Item | Status | Evidence / why |
|---|---|---|
| Farmer can access the application | ✅ | Farmer app, three demo farmers per state + registration |
| Farmer can create/select a field | ✅ | Demo farmer buttons; *Register a new field* with village search and polygon drawing |
| Farmer can specify crop and location | ✅ | State, district, village, crop, sowing date, irrigation, optional area |
| Farm intelligence is displayed | ✅ | `GET /api/fields/{id}/intelligence` → section 2 |
| Weather is displayed | ✅ | Live Open-Meteo (sample fallback, labelled) |
| Soil data is displayed | ✅ | Soil Health Card record via state adapter + live SoilGrids texture |
| Satellite/vegetation data is displayed | ⚠️ | NDVI series and chart shown; **sample** series until the project's Earth Engine registration is approved (live code path complete, probe reports the reason) |
| Farm health score is displayed | ✅ | Weighted score with factor breakdown |

### AI experience
| Item | Status | Evidence / why |
|---|---|---|
| Gemini generates contextual agro-advisory | ✅ | Gemini 2.5 Flash on Vertex AI, schema-validated, versioned |
| Crop recommendation works | ✅ | ≥ 3 options, rule scores + Gemini explanation |
| Gemini multimodal analyzes crop images | ✅ | Crop Doctor sends the photo to Gemini; photo stored in Cloud Storage |
| Potential disease/stress is displayed | ✅ | Potential condition + alternatives |
| Confidence/uncertainty is displayed | ✅ | Confidence, severity, expert-review flag, disclaimer |
| Regenerative recommendation is displayed | ✅ | One field-specific practice per advisory |

### Language & voice
| Item | Status | Evidence / why |
|---|---|---|
| English supported | ✅ | |
| Hindi supported | ✅ | UI + Cloud Translation of advisories (UI strings need native review) |
| Telugu supported | ✅ | UI + Cloud Translation; Telugu speech in/out |
| At least one complete voice interaction works | ✅ | Cloud STT → Gemini answer grounded in field context → Cloud TTS (verified with Telugu audio); browser fallback on Safari |

### Agriculture officer
| Item | Status | Evidence / why |
|---|---|---|
| Officer dashboard exists | ✅ | `apps/officer-dashboard` |
| State/district intelligence is visible | ✅ | India → state → district → block, served from BigQuery (synthetic, labelled) |
| Risk indicators are visible | ✅ | Farm Health, weather risk, water stress, alerts |
| Disease/stress hotspots are visible | ✅ | Hotspot list + recent Crop Doctor results |

### Interoperability
| Item | Status | Evidence / why |
|---|---|---|
| Canonical schema is documented | ✅ | `data/schemas/*.schema.json` generated from Pydantic models |
| At least two state configurations exist | ✅ | AP, Maharashtra, Punjab (`data/adapters/`) |
| State-specific data can map to the common schema | ✅ | Adapter engine + *Interoperability* tab + tests |
| Shared AI/API services operate on the common structure | ✅ | All endpoints take canonical records |

### Deployment & submission
| Item | Status | Evidence / why |
|---|---|---|
| Prototype is publicly deployed | ⚠️ | Images build and run locally in Docker; `infrastructure/cloud-run/deploy.sh` deploys all three services. **Running the deploy is pending approval** at the time of writing; URLs above are the deterministic Cloud Run addresses the script produces |
| Source code is available through GitHub | ✅ | Public repo |
| README contains setup and architecture documentation | ✅ | README: architecture diagram, integration map, env vars, run, onboarding |
| Demo data is available | ✅ | `data/sample/` (labelled) + BigQuery table |
| 3-5 minute demo video is prepared | ❌ | Script above is ready; recording needs a human with the live URLs |
| 10-12 slide pitch deck is prepared | ✅ | `docs/pitch/agri-ai-network-pitch.pptx` (generated by `docs/pitch/build_deck.py`) |
| 2-3 line product description is prepared | ✅ | Top of this document |

### Outside the DoD, still open
- Firestore (Firebase not yet added): records are per-instance SQLite on Cloud Run (`max-instances=1`).
- No authentication (Firebase Auth planned); the two roles are separate apps.
- Browser Maps key: rejected on `http://localhost:3040` during local testing (`RefererNotAllowedMapError`); the apps
  fall back to OpenStreetMap automatically and say so. Allowed on `https://*.run.app` per the key restriction.

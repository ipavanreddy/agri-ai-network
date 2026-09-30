// Agri AI Network pitch deck (Spontom style). Build: `npm install && node build-deck.js`.
// Every number on the slides comes from docs/PRD.md, the running prototype (30 Sep 2026) or a cited source.
const kit = require("./deck-kit");
const A = (f) => __dirname + "/assets/" + f;

// Live links: edit here (e.g. to swap in friendly Firebase Hosting URLs).
const LINKS = [
  { label: "Farmer app", url: "https://agri-ai-network-farmer-web-847963771142.asia-south1.run.app" },
  { label: "Officer dashboard", url: "https://agri-ai-network-officer-dashboard-847963771142.asia-south1.run.app" },
  { label: "API (+ /docs)", url: "https://agri-ai-network-api-847963771142.asia-south1.run.app" },
  { label: "Source", url: "https://github.com/ipavanreddy/agri-ai-network" },
];

const content = {
  meta: { product: "Agri AI Network", title: "pitch deck" },
  slides: [
    {
      type: "cover", kicker: "Build with AI (Google)  •  Track 4", product: "Agri AI\nNetwork",
      tagline: "From scattered farm data\nto one field-level decision.",
      subtitle: "An interoperable AI advisory layer for India's smallholder farmers, with district intelligence for agriculture officers.",
      pills: ["Gemini-grounded", "Officer-reviewed", "State-agnostic"], image: A("cover-farm-health.png"),
      imageCaption: "Live prototype: Farm Health for a sample 2.4-acre groundnut field in Anantapur, AP",
      byline: "A concept proposal and working prototype by Spontom Enterprise Private Limited",
      dateline: "DPIIT Recognised  •  Visakhapatnam  •  September 2026",
      notes: "Agri AI Network gives a smallholder farmer one advisor for their own field. It joins live weather, Soil Health Card data and satellite vegetation into an explainable Farm Health score, then uses Gemini to turn that into a grounded advisory, crop options and a photo-based Crop Doctor. The same canonical data model lets any state plug in its records and gives agriculture officers a district risk view. What you see on the right is a real screenshot of the running prototype.",
    },
    {
      type: "problem", section: "01 — Problem understanding", title: "The data exists. It rarely meets at the field decision.",
      subtitle: "Weather, soil, satellite and state records sit in separate systems; the farmer gets generic advice.",
      card: {
        heading: "One small field, many disconnected signals.",
        stats: [{ n: "~86%", label: "holders small/marginal" }, { n: "2.4", label: "acres (demo field)" }, { n: "0.32", label: "NDVI vs ~0.62 expected" }],
        story: "Lakshmi's groundnut is half as green as expected for its stage. Her soil card, forecast and satellite view never meet in one answer.",
        pill: "THE LAST-MILE GAP",
      },
      flow: [{ title: "DATA", desc: "Forecast, soil card, satellite, records" }, { title: "ADVICE", desc: "District or block level, generic" },
        { title: "?", desc: "No field-level synthesis", gap: true }, { title: "DECISION", desc: "Guesswork or delay" }],
      focused: "Farmers lack one timely advisor that combines their own field's data and explains itself.",
      consequence: "Late disease response, mistimed irrigation and soil decline; officers see risk only after it spreads.",
      footnote: "[1] Agriculture Census 2015-16, via PIB (2023).  Field figures: sample farmer record; NDVI is live Sentinel-2 over the sample field polygon (14 Sep 2026).",
      notes: "About 86 percent of India's operational holders are small or marginal, per the Agriculture Census cited here. The information they need exists: forecasts, Soil Health Cards, satellite imagery and state records, but it lives in separate systems. Our demo farmer's field shows it: satellite greenness is 0.32 against roughly 0.62 expected, yet nothing joins that to her soil card and forecast. The gap is not more data; it is a field-level synthesis the farmer can act on.",
    },
    {
      type: "solution", section: "02 — Proposed solution", title: "One advisor for the farmer's own field, grounded in data.",
      subtitle: "Signals become a transparent score; Gemini explains and recommends; a human releases the advice.",
      steps: [
        { title: "FARM INTELLIGENCE", desc: "Weather, soil card and Sentinel-2 NDVI become an explainable Farm Health score." },
        { title: "GROUNDED ADVICE", desc: "Gemini reasons only over that context: observed, interpreted, action. English, Hindi, Telugu.", highlight: true },
        { title: "HUMAN REVIEW", desc: "An Agriculture Officer approves each AI output; Crop Doctor names the nearest agri office.", coral: true },
      ],
      panel: {
        header: "TODAY'S ADVISORY", badge: "Gemini • schema-checked", title: "Groundnut • pod development • day 80 • rainfed",
        items: ["Observed: NDVI 0.32 vs ~0.62 expected (Sentinel-2, 14 Sep).", "Observed: organic carbon 0.38%, N 176 kg/ha (soil card, sample).",
          "Within 48 h: scout the field for Early Leaf Spot symptoms.", "Within 48 h: ask the KVK or officer to confirm on site."],
        fallback: "Regenerative: return groundnut residue to the soil after harvest.",
        footer: "Risk: high • confidence 55% • awaiting review", button: "Listen (TTS)",
      },
      footnote: "Excerpt of a real advisory from gemini-2.5-flash (prompt advisory_v1), 30 Sep 2026. The soil record is a labelled synthetic sample.",
      notes: "The solution has three parts. First, weather, soil and satellite signals become a Farm Health score with a visible breakdown. Second, Gemini reasons only over that structured context and must return schema-validated JSON that separates observations, interpretation and actions. The panel on the right is an excerpt of a real advisory the prototype generated today; note that it cites its sources and flags its own uncertainty. Third, every AI output waits for an Agriculture Officer's approval.",
    },
    {
      type: "loop", section: "03 — How it works", title: "From field signal to reviewed action in seven steps.",
      subtitle: "Rules where rules suffice, Gemini where reasoning helps, a person where consequences matter.", highlight: 3,
      flow: [{ title: "Field", desc: "Map or state record" }, { title: "Sense", desc: "Weather • soil • NDVI" }, { title: "Score", desc: "Farm Health 0–100" },
        { title: "Advise", desc: "Gemini, JSON schema" }, { title: "Diagnose", desc: "Leaf photo → Gemini" }, { title: "Localise", desc: "en • hi • te • voice" }, { title: "Review", desc: "Officer approves" }],
      tiers: [
        { label: "Tier 0 • Rules", text: "Farm Health and crop scores are transparent rules. Missing factors are re-weighted, never imputed." },
        { label: "Tier 1 • Bounded AI", text: "Gemini advisory, crop reasons and Crop Doctor; each record stores model and prompt version." },
        { label: "Tier 2 • Human", text: "Officer approves or rejects. Low-confidence or severe Crop Doctor results go to expert review." },
      ],
      assumptionLabel: "Design rule", assumption: "The farmer sees AI output labelled as a draft awaiting review; nothing is auto-approved.",
      footnote: "Farm Health weights: vegetation 30% • soil 25% • weather 20% • water 15% • crop condition 10% (PRD §11; services/api/app/intelligence/health.py).",
      notes: "Here is the loop. A field comes from a map drawing or a state record; weather, soil and satellite are fetched with source and timestamp; a rule-based Farm Health score is computed. Gemini then produces the advisory and, from a leaf photo, a preliminary Crop Doctor assessment. The result is localised to Hindi or Telugu and can be spoken. Three tiers keep this safe: deterministic rules first, bounded AI second, and a human officer for every consequential output.",
    },
    {
      type: "users", section: "04 — Users & context", title: "Design for Lakshmi first; connect the officer above her.",
      subtitle: "Exactly two app roles (PRD §7): Farmer and Agriculture Officer. KVKs and states connect through data.",
      image: A("farmer-crop-doctor.png"), imageLabel: "Lakshmi Devi  •  Primary user (sample)",
      imageCaption: "2.4 acres • rainfed groundnut • Anantapur, Andhra Pradesh",
      people: [
        { name: "Farmer", role: "Primary user", desc: "Needs one clear next action in Telugu, by voice, with sources shown." },
        { name: "Agri Officer", role: "District view", desc: "Needs district and block risk, hotspots and a review queue, not raw feeds." },
        { name: "KVK", role: "Expert referral", desc: "Confirms Crop Doctor cases; Maps shows the nearest office and drive time." },
        { name: "State dept.", role: "Data owner", desc: "Keeps its own records; joins through a declarative adapter, not a rebuild." },
      ],
      constraints: [{ label: "Literacy", text: "voice • 3 languages" }, { label: "Data gaps", text: "source + age badges" }, { label: "AI error", text: "officer + KVK check" }],
      footnote: "Personas are sample records from the AP/MH/PB adapters. Screenshot: Crop Doctor on the synthetic sample leaf, live Gemini + Google Maps.",
      notes: "Our primary user is a smallholder like Lakshmi, a sample farmer with 2.4 rainfed acres of groundnut in Anantapur. She needs one clear action in her language, by voice if she prefers, and she needs to see where each fact came from. Around her are the Agriculture Officer, who needs a district risk view and a review queue; the KVK, which confirms Crop Doctor cases; and the state department, which keeps its data and joins through an adapter. The screenshot shows Crop Doctor pointing to the nearest agriculture office with drive time.",
    },
    {
      type: "journey", section: "05 — Journey", title: "Lakshmi's field, end to end, in one continuous demo.",
      subtitle: "PRD §43 Scenario A: Andhra Pradesh • Anantapur • groundnut • 2.4 acres. Sample farmer, live data feeds.",
      steps: [
        { label: "Sense", title: "Farm Health 73 / 100", desc: "Vegetation 51 • soil 70 • weather 100 • water 96 • crop 55" },
        { label: "Advise", title: "Risk high, next 48 h", desc: "Scout for leaf spot; low organic carbon 0.38%, N 176 kg/ha" },
        { label: "Diagnose", title: "Early Leaf Spot, 80%", desc: "Moderate severity; Late Leaf Spot (70%) as alternative", highlight: true },
        { label: "Act", title: "Nearest support: ~36 min", desc: "Agricultural college 20.3 km by road (Places + Routes)" },
      ],
      panel: {
        kicker: "Officer view", headline: "Anantapur is the AP hotspot.", sub: "Synthetic BigQuery indicators:",
        items: ["18 disease / stress alerts", "Farm Health 56, water stress 0.70", "Lakshmi's advisory in review queue"],
        whyLabel: "Next season", why: "Bajra 96 • foxtail millet 96 • jowar 91 • green gram 86 • red gram 85 (rule score, explained by Gemini).",
      },
      footnote: "Values from the running prototype on 30 Sep 2026; live weather and NDVI change daily. District indicators are labelled synthetic samples.",
      notes: "This is the demo story with the numbers the prototype produced today. Lakshmi's Farm Health is 73, pulled down by low vegetation and a soil card with low organic carbon and nitrogen. Gemini rates the risk high for the next 48 hours and asks her to scout for leaf spot; Crop Doctor, from a sample leaf photo, suggests Early Leaf Spot at 80 percent confidence and names the nearest agriculture office, about 36 minutes away. On the officer side, Anantapur shows up as the state's hotspot, and her advisory sits in the review queue.",
    },
    {
      type: "table", section: "06 — Innovation & differentiation", title: "Not another portal: a field layer that joins them.",
      subtitle: "India's public systems each solve a valuable part; Agri AI Network composes them per field.",
      columns: ["Approach", "What it contributes", "Remaining gap for the field decision"],
      rows: [
        ["Kisan Call Centre", "Toll-free expert answers in 22 languages [4]", "Answers a call; does not see the field's own data"],
        ["GKMS agromet", "District / block weather-based advisories, IMD with ICAR [3]", "Block level, not field level; no photo or soil card link"],
        ["Soil Health Card", "Lab-tested N, P, K, pH, organic carbon per sample [5]", "Static card, not joined with weather or crop stage"],
        ["Digital Agri Mission", "AgriStack, Krishi DSS and soil maps as national DPI [2]", "Infrastructure layer; farmer-facing advice is left to apps"],
        ["Agri AI Network", "Field context + Gemini advice + photo check + officer review", "Prototype on sample state data; not yet field-validated"],
      ],
      calloutLabel: "Distinctive capability", callout: "Consumes public-system data through state adapters instead of replacing them.",
      footnote: "[2] PIB, Digital Agriculture Mission (2024).  [3] PIB, GKMS (2023).  [4] PIB, Kisan Call Centre (2021).  [5] Soil Health Card portal.",
      notes: "We are not competing with India's agricultural systems. The Kisan Call Centre answers farmers in 22 languages, GKMS issues district and block agromet advisories, the Soil Health Card measures nutrients, and the Digital Agriculture Mission is building AgriStack and the Krishi Decision Support System. What none of them does alone is join a specific field's soil, weather, satellite and photo evidence into one explained action. That is our layer, and our own limit is stated plainly: it is a prototype on sample state data.",
    },
    {
      type: "tech", section: "07 — Technology & Google AI", title: "Bounded Gemini on a canonical, state-agnostic model.",
      subtitle: "Every data block carries source and timestamp; AI returns schema-validated JSON or falls back to rules.",
      rows: [
        { title: "Channels", desc: "Farmer web app (en / hi / te, voice) • Officer dashboard • Next.js 16" },
        { title: "State adapters", desc: "AP e-Crop, MahaDBT, Punjab land-record formats → one canonical schema" },
        { title: "Data layer", desc: "Open-Meteo • Soil Health Card + SoilGrids • Sentinel-2 via Earth Engine • BigQuery" },
        { title: "AI layer", desc: "Gemini 2.5 Flash on Vertex AI • Pydantic-validated JSON • model + prompt version", highlight: true },
        { title: "Delivery", desc: "FastAPI + both apps on Cloud Run • private Cloud Storage • Secret Manager" },
      ],
      navy: {
        title: "Google AI integration map",
        bullets: ["Gemini 2.5 Flash: advisory, Q&A, Crop Doctor (multimodal)",
          "Speech-to-Text, Text-to-Speech, Translation", "Earth Engine • Maps Places / Routes • BigQuery"],
        pillLabel: "Pending", pillText: "Firestore + Firebase Auth: SQLite fallback today",
      },
      gate: {
        title: "Real vs demo gate",
        rows: [{ label: "Probed live", text: "Each integration is tested with a real call before it is badged Live" },
          { label: "Labelled sample", text: "State exports, district indicators, sample leaf: synthetic in data + UI", coral: true }],
      },
      footnote: "[6] Sentinel-2 SR Harmonized on Earth Engine.  [7] Open-Meteo; ISRIC SoilGrids.  Status from /api/system/status, local run, 30 Sep 2026.",
      notes: "The architecture is layered. State adapters map three different state record formats into one canonical schema, so every shared service runs unchanged. The data layer uses live Open-Meteo weather, SoilGrids texture, Sentinel-2 NDVI through Earth Engine and BigQuery for regional indicators. Gemini 2.5 Flash on Vertex AI is bounded: it receives structured context and must return validated JSON, and every record stores model and prompt versions. The gate card is our honesty rule: an integration is shown as Live only after a real probe call succeeds, and all sample data is labelled.",
    },
    {
      type: "responsible", section: "08 — Responsible AI & data", title: "Advice that shows its evidence and waits for a human.",
      subtitle: "Gemini never invents measurements; the officer, not the model, releases consequential advice.",
      left: {
        pills: ["AI draft", "Awaiting Agriculture Officer review"],
        rows: [{ label: "Evidence first", text: "Observed data, AI interpretation and action are separate fields, each citing its source." },
          { label: "Contestable", text: "The officer approves or rejects with a note; the farmer sees the status." }],
      },
      dont: { label: "Do not do", items: ["Certified diagnosis or pesticide prescriptions", "Invent or impute missing measurements", "Collect identity documents or bank details"] },
      safety: {
        title: "Safety by design",
        rows: [
          { label: "Grounding", text: "Structured field context only; validated JSON, else a rules fallback." },
          { label: "Uncertainty", text: "Confidence, missing information and data-age notes in every advisory." },
          { label: "Crop Doctor", text: "“Potential condition” wording; low confidence or high severity → expert." },
          { label: "Provenance", text: "Source, timestamp and a Live / Sample badge on every data block." },
          { label: "Traceability", text: "Each AI record stores model name, model version and prompt version." },
          { label: "Security", text: "Keys in Secret Manager; crop photos in a private bucket; no secrets in git." },
        ],
      },
      footnote: "Known gaps: no authentication yet (Firebase Auth planned); Hindi / Telugu strings need native-speaker review (README, Known gaps).",
      notes: "Responsible AI here is concrete. Gemini only sees structured field data and must separate what was observed from what it infers and what it recommends; if validation fails, the system falls back to deterministic rules. Crop Doctor always speaks of a potential condition, never a certified diagnosis, and routes low-confidence or severe cases to an expert. We state the gaps too: authentication is not built yet, and the Hindi and Telugu strings need native-speaker review.",
    },
    {
      type: "outcomes", section: "09 — Outcomes, validation & scale", title: "Earn the right to scale: one district, then one state.",
      subtitle: "The first proof is not app usage; it is timelier, correct action on the field.",
      chain: [{ title: "Trust", desc: "Officers approve AI drafts with few edits" }, { title: "Action", desc: "Farmers act within the advised window" },
        { title: "Timeliness", desc: "Earlier disease and irrigation response" }, { title: "Outcome", desc: "Water use, crop loss, soil health improve" }],
      measure: { items: ["Officer approve / edit / reject rate", "Crop Doctor vs KVK-confirmed cases", "Advisory follow-up by farmers", "PRD §49.2 impact indicators"] },
      gates: [
        { title: "District pilot", desc: "One district, e.g. Anantapur, KVK-linked blocks vs matched blocks" },
        { title: "Real feeds", desc: "Swap sample exports for state soil card / crop-booking feeds via adapter" },
        { title: "Claim carefully", desc: "Measure diagnosis accuracy vs KVK labels before any scale claim" },
      ],
      budget: { text: "Candidate route: Digital Agriculture Mission (₹2,817 cr, Krishi DSS component) with state co-funding; to confirm with the department. [2]" },
      ownership: { title: "Ownership + scale", rows: [{ label: "Owner", text: "State Department of Agriculture" },
        { label: "Channel", text: "Agriculture Officers + KVKs + agromet units" }, { label: "Gate", text: "Data-sharing MoU • language QA • accuracy" }] },
      footnote: "Pilot design and measures are proposals to validate with a state partner; no field results exist yet. Scale path follows PRD §50 (district → state → national).",
      notes: "We want to earn scale, not assume it. The outcome chain starts with officer trust, measured by how often they approve AI drafts unedited, then farmer action, then timeliness, and only then field outcomes like water use and crop loss. A first district pilot, for example Anantapur, would compare KVK-linked blocks with matched blocks and check Crop Doctor against KVK-confirmed cases. The natural owner is the state agriculture department; the Digital Agriculture Mission, with its Krishi Decision Support System component, is a candidate funding route that we would confirm with the department.",
    },
    {
      type: "live", section: "10 — Live prototype", title: "Working today, end to end, on Google Cloud.",
      subtitle: "Real screenshots from the running prototype, 30 Sep 2026: sample farmer, live Gemini, weather and NDVI.",
      screens: [{ image: A("farmer-app.png"), caption: "Farmer app: Farm Health + live data" }, { image: A("officer-dashboard.png"), caption: "Officer: AP district risk (synthetic)" }],
      links: LINKS,
      criteria: [
        { weight: "25%", label: "AI / technical execution", how: "Gemini text + multimodal, schema-validated and versioned; Earth Engine, Speech, Translation" },
        { weight: "20%", label: "Problem-solution fit", how: "PRD §8 journey end to end: field data → advisory → photo check → action" },
        { weight: "20%", label: "Depth & reach across India", how: "3 states via declarative adapters; English, Hindi, Telugu; voice in and out" },
        { weight: "20%", label: "Deployability & scalability", how: "Three Cloud Run services, one deploy script, API-first canonical schema" },
        { weight: "15%", label: "Impact potential", how: "~86% of holders are small or marginal [1]; view scales district → state" },
      ],
      notes: "Everything shown is working software. On the left, the farmer app with the Farm Health breakdown and live weather and satellite data; next to it, the officer dashboard's Andhra Pradesh district risk map, served from BigQuery with labelled synthetic indicators. The links go to the Cloud Run services and the public repository. On the right is how we map to the five evaluation criteria, weighted as in the brief.",
    },
    {
      type: "references", section: "Appendix — References", title: "Evidence and public-system sources",
      subtitle: "Numbered references correspond to citations on the core slides.",
      refs: [
        { n: 1, title: "PIB: Livelihood of Farmers (2023)", desc: "Ministry of Agriculture & FW, 14 Mar 2023: per Agriculture Census 2015-16, small and marginal holders are about 86% of operational holders.", url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1906888" },
        { n: 2, title: "PIB: Digital Agriculture Mission (2024)", desc: "Cabinet approval, 2 Sep 2024: ₹2,817 crore outlay; DPIs AgriStack, Krishi Decision Support System and Soil Profile Mapping.", url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2050966" },
        { n: 3, title: "PIB: Gramin Krishi Mausam Sewa (2023)", desc: "IMD with ICAR renders district / block-level agrometeorological advisory services to farmers.", url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1906389" },
        { n: 4, title: "PIB: Kisan Call Centre (2021)", desc: "“Addressing Queries of Farmers in 22 languages”, 3 Aug 2021: replies in 22 official languages.", url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1741969" },
      ],
      notes: "These are the public sources behind the problem and differentiation slides. The 86 percent figure is from the Agriculture Census 2015-16 as reported by the Ministry of Agriculture through PIB. The Digital Agriculture Mission, GKMS and Kisan Call Centre descriptions are taken from official PIB releases.",
    },
    {
      type: "references", section: "Appendix — References", title: "Data, platform and project sources",
      subtitle: "Datasets and services the prototype uses; full list in THIRD_PARTY.md.",
      refs: [
        { n: 5, title: "Soil Health Card portal", desc: "Government of India scheme; N, P, K rating thresholds used in the Farm Health soil factor. Sample records follow its format.", url: "https://soilhealth.dac.gov.in" },
        { n: 6, title: "Sentinel-2 SR Harmonized", desc: "Copernicus Sentinel-2 surface reflectance on Google Earth Engine; field-mean NDVI / NDMI time series.", url: "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED" },
        { n: 7, title: "Open-Meteo; ISRIC SoilGrids 2.0", desc: "Live forecast, 14-day history and soil moisture (CC BY 4.0); modelled soil texture at 250 m (soilgrids.org, CC BY 4.0).", url: "https://open-meteo.com" },
        { n: 8, title: "Agri AI Network PRD + repository", desc: "docs/PRD.md (scenarios, Farm Health weights, evaluation weights), README and the source code behind every prototype number.", url: "https://github.com/ipavanreddy/agri-ai-network", tag: "Source repo" },
      ],
      notes: "The second reference slide lists the data sources the prototype actually uses: the Soil Health Card format and thresholds, Sentinel-2 through Earth Engine, Open-Meteo weather and ISRIC SoilGrids. The last entry is our own PRD and repository, which is where every prototype number on these slides can be traced.",
    },
  ],
};

kit.build(content, __dirname + "/Agri_AI_Network_Spontom_Pitch.pptx").then((p) => console.log("wrote", p));

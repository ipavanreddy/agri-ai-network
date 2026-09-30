"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Lang } from "@/lib/types";

// UI strings. Hindi/Telugu are hand-written demo translations; review with native speakers before release.
const STRINGS = {
  app_title: { en: "Agri AI Network", hi: "एग्री एआई नेटवर्क", te: "అగ్రి ఏఐ నెట్‌వర్క్" },
  tagline: {
    en: "Your field, weather, soil and satellite - one advisor",
    hi: "आपका खेत, मौसम, मिट्टी और उपग्रह - एक सलाहकार",
    te: "మీ పొలం, వాతావరణం, నేల, ఉపగ్రహం - ఒకే సలహాదారు",
  },
  language: { en: "Language", hi: "भाषा", te: "భాష" },
  step_field: { en: "1. My field", hi: "1. मेरा खेत", te: "1. నా పొలం" },
  step_intel: { en: "2. Farm intelligence", hi: "2. खेत की जानकारी", te: "2. పొలం సమాచారం" },
  step_advisory: { en: "3. Today's advisory", hi: "3. आज की सलाह", te: "3. నేటి సలహా" },
  step_crops: { en: "4. Crop recommendations", hi: "4. फसल सुझाव", te: "4. పంట సిఫార్సులు" },
  step_doctor: { en: "5. Crop Doctor", hi: "5. क्रॉप डॉक्टर", te: "5. క్రాప్ డాక్టర్" },
  step_voice: { en: "6. Ask by voice", hi: "6. बोलकर पूछें", te: "6. మాట్లాడి అడగండి" },
  demo_farmers: { en: "Demo farmers (from state adapters)", hi: "डेमो किसान (राज्य एडेप्टर से)", te: "డెమో రైతులు (రాష్ట్ర అడాప్టర్ల నుండి)" },
  new_field: { en: "Register a new field", hi: "नया खेत दर्ज करें", te: "కొత్త పొలం నమోదు" },
  draw_hint: {
    en: "Tap the map to mark the corners of your field (at least 3 points).",
    hi: "अपने खेत के कोने चिह्नित करने के लिए नक्शे पर टैप करें (कम से कम 3 बिंदु)।",
    te: "మీ పొలం మూలలను గుర్తించడానికి మ్యాప్‌పై నొక్కండి (కనీసం 3 బిందువులు).",
  },
  clear: { en: "Clear", hi: "मिटाएँ", te: "తొలగించు" },
  name: { en: "Farmer name", hi: "किसान का नाम", te: "రైతు పేరు" },
  state: { en: "State", hi: "राज्य", te: "రాష్ట్రం" },
  district: { en: "District", hi: "ज़िला", te: "జిల్లా" },
  village: { en: "Village", hi: "गाँव", te: "గ్రామం" },
  crop: { en: "Crop", hi: "फसल", te: "పంట" },
  sowing_date: { en: "Sowing date", hi: "बुवाई की तारीख", te: "విత్తిన తేదీ" },
  irrigation: { en: "Irrigation", hi: "सिंचाई", te: "నీటి పారుదల" },
  save_field: { en: "Save field", hi: "खेत सहेजें", te: "పొలం సేవ్ చేయండి" },
  area: { en: "Area", hi: "क्षेत्रफल", te: "విస్తీర్ణం" },
  acres: { en: "acres", hi: "एकड़", te: "ఎకరాలు" },
  stage: { en: "Stage", hi: "अवस्था", te: "దశ" },
  days_after_sowing: { en: "days after sowing", hi: "बुवाई के बाद दिन", te: "విత్తిన తర్వాత రోజులు" },
  farm_health: { en: "Farm Health", hi: "फार्म हेल्थ", te: "ఫార్మ్ హెల్త్" },
  weather: { en: "Weather", hi: "मौसम", te: "వాతావరణం" },
  soil: { en: "Soil", hi: "मिट्टी", te: "నేల" },
  satellite: { en: "Satellite", hi: "उपग्रह", te: "ఉపగ్రహం" },
  water: { en: "Water", hi: "पानी", te: "నీరు" },
  vegetation: { en: "Vegetation", hi: "वनस्पति", te: "పచ్చదనం" },
  crop_condition: { en: "Crop condition", hi: "फसल की स्थिति", te: "పంట స్థితి" },
  rain_14d: { en: "Rain, last 14 days", hi: "बारिश, पिछले 14 दिन", te: "వర్షం, గత 14 రోజులు" },
  rain_3d: { en: "Rain forecast, 3 days", hi: "बारिश पूर्वानुमान, 3 दिन", te: "వర్ష సూచన, 3 రోజులు" },
  humidity: { en: "Humidity", hi: "आर्द्रता", te: "తేమ" },
  temperature: { en: "Temperature", hi: "तापमान", te: "ఉష్ణోగ్రత" },
  organic_carbon: { en: "Organic carbon", hi: "जैविक कार्बन", te: "సేంద్రియ కర్బనం" },
  ndvi: { en: "Crop greenness (NDVI)", hi: "फसल हरियाली (NDVI)", te: "పంట పచ్చదనం (NDVI)" },
  generate_advisory: { en: "Generate advisory", hi: "सलाह बनाएँ", te: "సలహా రూపొందించండి" },
  observed: { en: "Observed data", hi: "देखा गया डेटा", te: "గమనించిన డేటా" },
  interpretation: { en: "AI interpretation", hi: "एआई व्याख्या", te: "ఏఐ విశ్లేషణ" },
  recommendation: { en: "Recommended actions", hi: "सुझाए गए कदम", te: "సూచించిన చర్యలు" },
  regenerative: { en: "Regenerative practice", hi: "पुनर्योजी खेती अभ्यास", te: "పునరుత్పాదక సాగు పద్ధతి" },
  risk: { en: "Risk", hi: "जोखिम", te: "ప్రమాదం" },
  confidence: { en: "Confidence", hi: "विश्वास", te: "నమ్మకం" },
  missing_info: { en: "Missing information", hi: "अनुपलब्ध जानकारी", te: "లేని సమాచారం" },
  freshness: { en: "Data freshness", hi: "डेटा की ताज़गी", te: "డేటా తాజాదనం" },
  listen: { en: "Listen", hi: "सुनें", te: "వినండి" },
  pending_review: {
    en: "AI draft - awaiting Agriculture Officer review",
    hi: "एआई मसौदा - कृषि अधिकारी की समीक्षा बाकी",
    te: "ఏఐ ముసాయిదా - వ్యవసాయ అధికారి సమీక్ష కోసం వేచి ఉంది",
  },
  approved: { en: "Reviewed and approved by Agriculture Officer", hi: "कृषि अधिकारी द्वारा स्वीकृत", te: "వ్యవసాయ అధికారి ఆమోదించారు" },
  rejected: { en: "Rejected by Agriculture Officer - do not act on it", hi: "कृषि अधिकारी द्वारा अस्वीकृत", te: "వ్యవసాయ అధికారి తిరస్కరించారు" },
  get_recommendations: { en: "Recommend crops", hi: "फसल सुझाएँ", te: "పంటలు సూచించండి" },
  suitability: { en: "Suitability", hi: "उपयुक्तता", te: "అనుకూలత" },
  rotation_plan: { en: "Rotation plan", hi: "फसल चक्र योजना", te: "పంట మార్పిడి ప్రణాళిక" },
  upload_photo: { en: "Upload crop photo", hi: "फसल की फोटो डालें", te: "పంట ఫోటో అప్‌లోడ్ చేయండి" },
  use_sample_photo: { en: "Use sample leaf photo", hi: "नमूना पत्ती फोटो", te: "నమూనా ఆకు ఫోటో" },
  analyse: { en: "Analyse photo", hi: "फोटो जाँचें", te: "ఫోటో విశ్లేషించండి" },
  potential_condition: { en: "Potential condition", hi: "संभावित समस्या", te: "సంభావ్య సమస్య" },
  visible_symptoms: { en: "Visible symptoms", hi: "दिखने वाले लक्षण", te: "కనిపించే లక్షణాలు" },
  severity: { en: "Severity", hi: "गंभीरता", te: "తీవ్రత" },
  next_steps: { en: "Recommended next steps", hi: "अगले कदम", te: "తదుపరి చర్యలు" },
  ask_placeholder: { en: "Type or speak your question...", hi: "अपना सवाल लिखें या बोलें...", te: "మీ ప్రశ్నను టైప్ చేయండి లేదా చెప్పండి..." },
  speak: { en: "Speak", hi: "बोलें", te: "మాట్లాడండి" },
  stop: { en: "Stop", hi: "रोकें", te: "ఆపండి" },
  ask: { en: "Ask", hi: "पूछें", te: "అడగండి" },
  select_field_first: { en: "Select or register a field first.", hi: "पहले खेत चुनें या दर्ज करें।", te: "ముందుగా పొలాన్ని ఎంచుకోండి లేదా నమోదు చేయండి." },
  sample_toggle: {
    en: "Use sample scenario data (offline demo)",
    hi: "नमूना परिदृश्य डेटा (ऑफ़लाइन डेमो)",
    te: "నమూనా సన్నివేశ డేటా (ఆఫ్‌లైన్ డెమో)",
  },
  loading: { en: "Loading...", hi: "लोड हो रहा है...", te: "లోడ్ అవుతోంది..." },
  example_questions: { en: "Try", hi: "आज़माएँ", te: "ప్రయత్నించండి" },
} as const;

export type StringKey = keyof typeof STRINGS;

export const EXAMPLE_QUESTIONS: Record<Lang, string[]> = {
  en: ["Should I irrigate this week?", "Is there disease risk?", "Which crop should I sow next season?"],
  hi: ["क्या इस हफ्ते सिंचाई करूँ?", "क्या रोग का खतरा है?", "अगली फसल कौन सी बोऊँ?"],
  te: ["ఈ వారం నీటి తడి ఇవ్వాలా?", "తెగులు ప్రమాదం ఉందా?", "తదుపరి సీజన్‌లో ఏ పంట వేయాలి?"],
};

export const LANG_LABELS: Record<Lang, string> = { en: "English", hi: "हिन्दी", te: "తెలుగు" };
export const SPEECH_LOCALE: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: StringKey) => string };
const I18nContext = createContext<Ctx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    if (typeof window === "undefined") return "en";
    try {
      const saved = window.localStorage.getItem("agri.lang");
      return saved === "hi" || saved === "te" ? saved : "en";
    } catch {
      return "en";
    }
  });
  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      window.localStorage.setItem("agri.lang", l);
    } catch {
      /* storage unavailable */
    }
  }, []);
  const value = useMemo<Ctx>(() => ({ lang, setLang, t: (k) => STRINGS[k][lang] ?? STRINGS[k].en }), [lang, setLang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): Ctx {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}

"""Message catalogue for DEMO-MODE (rule-based) advisories and voice answers, in English, Hindi and Telugu.

Live mode uses Gemini + Cloud Translation instead. Demo advisories store message codes + params, so
switching language re-renders the same analysis without recomputing it (PRD §17).
Hindi/Telugu strings are hand-written demo translations and should be reviewed by native speakers.
"""

from typing import Any

M: dict[str, dict[str, str]] = {
    # ---- summaries -----------------------------------------------------------------------------
    "sum.dry_rain_coming": {
        "en": "Your {crop} is under dry-spell stress, but rain is expected in the next 2-3 days.",
        "hi": "आपकी {crop} सूखे के कारण तनाव में है, लेकिन अगले 2-3 दिनों में बारिश की संभावना है।",
        "te": "మీ {crop} పంట వర్షాభావం వల్ల ఒత్తిడిలో ఉంది, కానీ రాబోయే 2-3 రోజుల్లో వర్షం పడే అవకాశం ఉంది.",
    },
    "sum.dry": {
        "en": "Your {crop} is under dry-spell stress and no significant rain is forecast.",
        "hi": "आपकी {crop} सूखे के कारण तनाव में है और अच्छी बारिश का पूर्वानुमान नहीं है।",
        "te": "మీ {crop} పంట వర్షాభావం వల్ల ఒత్తిడిలో ఉంది, గణనీయమైన వర్ష సూచన లేదు.",
    },
    "sum.wet_disease": {
        "en": "Wet and humid weather is raising disease risk in your {crop}.",
        "hi": "नमी और लगातार बारिश से आपकी {crop} में रोग का खतरा बढ़ रहा है।",
        "te": "తేమ, తడి వాతావరణం వల్ల మీ {crop} పంటకు తెగుళ్ల ప్రమాదం పెరుగుతోంది.",
    },
    "sum.heat": {
        "en": "Rising temperatures may stress your {crop} at this stage.",
        "hi": "बढ़ता तापमान इस अवस्था में आपकी {crop} पर दबाव डाल सकता है।",
        "te": "పెరుగుతున్న ఉష్ణోగ్రతలు ఈ దశలో మీ {crop} పంటపై ఒత్తిడి కలిగించవచ్చు.",
    },
    "sum.ok": {
        "en": "Your {crop} looks on track for its growth stage.",
        "hi": "आपकी {crop} अपनी अवस्था के अनुसार ठीक दिख रही है।",
        "te": "మీ {crop} పంట దాని ఎదుగుదల దశకు తగినట్లుగా బాగుంది.",
    },
    # ---- observations (restate supplied data only) ----------------------------------------------
    "obs.rain_past": {
        "en": "{rain14} mm rain in the last 14 days.",
        "hi": "पिछले 14 दिनों में {rain14} मिमी बारिश।",
        "te": "గత 14 రోజుల్లో {rain14} మి.మీ. వర్షం.",
    },
    "obs.rain_forecast": {
        "en": "{rain3} mm rain forecast in the next 3 days.",
        "hi": "अगले 3 दिनों में {rain3} मिमी बारिश का पूर्वानुमान।",
        "te": "రాబోయే 3 రోజుల్లో {rain3} మి.మీ. వర్ష సూచన.",
    },
    "obs.humidity": {"en": "Humidity is {rh}%.", "hi": "आर्द्रता {rh}% है।", "te": "గాలిలో తేమ {rh}%."},
    "obs.tmax": {
        "en": "Maximum temperature up to {tmax} °C in the next 7 days.",
        "hi": "अगले 7 दिनों में अधिकतम तापमान {tmax} °C तक।",
        "te": "రాబోయే 7 రోజుల్లో గరిష్ఠ ఉష్ణోగ్రత {tmax} °C వరకు.",
    },
    "obs.ndvi": {
        "en": "Crop greenness (NDVI) is {ndvi} on {date}; about {expected} is typical at this stage.",
        "hi": "{date} को फसल की हरियाली (NDVI) {ndvi} है; इस अवस्था में लगभग {expected} सामान्य है।",
        "te": "{date} నాటికి పంట పచ్చదనం (NDVI) {ndvi}; ఈ దశలో సుమారు {expected} సాధారణం.",
    },
    "obs.ndvi_change": {
        "en": "NDVI changed by {change} over the last ~30 days.",
        "hi": "पिछले ~30 दिनों में NDVI में {change} का बदलाव।",
        "te": "గత ~30 రోజుల్లో NDVI లో {change} మార్పు.",
    },
    "obs.soil_oc": {
        "en": "Soil organic carbon is {oc}% (soil test of {date}).",
        "hi": "मिट्टी में जैविक कार्बन {oc}% है ({date} की जाँच)।",
        "te": "నేలలో సేంద్రియ కర్బనం {oc}% ({date} నాటి పరీక్ష).",
    },
    "obs.soil_ph": {"en": "Soil pH is {ph}.", "hi": "मिट्टी का pH {ph} है।", "te": "నేల pH {ph}."},
    "obs.soil_n": {
        "en": "Available nitrogen is {n} kg/ha (low).",
        "hi": "उपलब्ध नाइट्रोजन {n} किग्रा/हेक्टेयर (कम) है।",
        "te": "లభ్య నత్రజని {n} కి.గ్రా./హె. (తక్కువ).",
    },
    "obs.soil_moisture": {
        "en": "Topsoil moisture is {sm} m³/m³.",
        "hi": "ऊपरी मिट्टी की नमी {sm} m³/m³ है।",
        "te": "పై నేల తేమ {sm} m³/m³.",
    },
    "obs.stage": {
        "en": "Crop is {das} days after sowing ({stage}).",
        "hi": "फसल बुवाई के {das} दिन बाद ({stage}) में है।",
        "te": "పంట విత్తిన {das} రోజుల తర్వాత ({stage}) దశలో ఉంది.",
    },
    "obs.health": {
        "en": "Farm Health score is {score}/100 ({band}).",
        "hi": "फार्म हेल्थ स्कोर {score}/100 ({band}) है।",
        "te": "ఫార్మ్ హెల్త్ స్కోరు {score}/100 ({band}).",
    },
    # ---- interpretations -----------------------------------------------------------------------
    "int.moisture_stress": {
        "en": "The crop is likely under moisture stress after the dry spell.",
        "hi": "सूखे के बाद फसल में नमी की कमी का तनाव होने की संभावना है।",
        "te": "వర్షాభావం తర్వాత పంటకు తేమ కొరత ఒత్తిడి ఉండే అవకాశం ఉంది.",
    },
    "int.rain_relief": {
        "en": "The expected rain should ease moisture stress if it arrives as forecast.",
        "hi": "पूर्वानुमान के अनुसार बारिश होने पर नमी का तनाव कम होना चाहिए।",
        "te": "సూచన ప్రకారం వర్షం పడితే తేమ ఒత్తిడి తగ్గుతుంది.",
    },
    "int.disease_risk": {
        "en": "Warm, humid and wet conditions raise the risk of fungal leaf disease.",
        "hi": "गर्म, नम और गीला मौसम पत्तों के फफूंद रोग का खतरा बढ़ाता है।",
        "te": "వెచ్చని, తేమతో కూడిన తడి వాతావరణం ఆకు శిలీంధ్ర తెగుళ్ల ప్రమాదాన్ని పెంచుతుంది.",
    },
    "int.waterlogging": {
        "en": "Recent heavy rain may cause waterlogging in low patches of the field.",
        "hi": "हाल की भारी बारिश से खेत के निचले हिस्सों में जलभराव हो सकता है।",
        "te": "ఇటీవలి భారీ వర్షాల వల్ల పొలంలోని పల్లపు భాగాల్లో నీరు నిలిచే అవకాశం ఉంది.",
    },
    "int.low_fertility": {
        "en": "Low organic carbon limits the soil's water holding and nutrient supply.",
        "hi": "कम जैविक कार्बन से मिट्टी की जल-धारण क्षमता और पोषक आपूर्ति सीमित होती है।",
        "te": "తక్కువ సేంద్రియ కర్బనం వల్ల నేల నీటి నిల్వ సామర్థ్యం, పోషకాల సరఫరా తగ్గుతాయి.",
    },
    "int.heat_risk": {
        "en": "High temperatures in the forecast may stress the crop at this stage.",
        "hi": "पूर्वानुमानित उच्च तापमान इस अवस्था में फसल पर दबाव डाल सकता है।",
        "te": "సూచనలోని అధిక ఉష్ణోగ్రతలు ఈ దశలో పంటపై ఒత్తిడి కలిగించవచ్చు.",
    },
    "int.on_track": {
        "en": "Crop greenness is close to what is expected for this stage.",
        "hi": "फसल की हरियाली इस अवस्था की अपेक्षा के करीब है।",
        "te": "పంట పచ్చదనం ఈ దశకు ఆశించిన స్థాయికి దగ్గరగా ఉంది.",
    },
    # ---- recommendations -----------------------------------------------------------------------
    "rec.delay_irrigation": {
        "en": "Delay irrigation and check soil moisture again after the expected rain.",
        "hi": "सिंचाई टालें और अपेक्षित बारिश के बाद मिट्टी की नमी फिर से जाँचें।",
        "te": "నీటి తడి వాయిదా వేసి, ఆశించిన వర్షం తర్వాత నేల తేమను మళ్లీ పరిశీలించండి.",
    },
    "rec.protective_irrigation": {
        "en": "Give a light protective irrigation in the next 2-3 days if water is available.",
        "hi": "पानी उपलब्ध हो तो अगले 2-3 दिनों में हल्की जीवनरक्षक सिंचाई करें।",
        "te": "నీరు అందుబాటులో ఉంటే రాబోయే 2-3 రోజుల్లో తేలికపాటి రక్షణ తడి ఇవ్వండి.",
    },
    "rec.conserve_moisture": {
        "en": "Conserve soil moisture: avoid deep hoeing and keep the soil surface covered.",
        "hi": "मिट्टी की नमी बचाएँ: गहरी गुड़ाई न करें और मिट्टी की सतह ढककर रखें।",
        "te": "నేల తేమను కాపాడండి: లోతుగా దున్నకండి, నేల ఉపరితలాన్ని కప్పి ఉంచండి.",
    },
    "rec.scout_disease": {
        "en": "Walk the field and check leaves on 10-15 plants for spots or pests; report any spread to the agriculture officer.",
        "hi": "खेत में घूमकर 10-15 पौधों की पत्तियों पर धब्बे या कीट देखें; फैलाव दिखे तो कृषि अधिकारी को बताएं।",
        "te": "పొలంలో తిరిగి 10-15 మొక్కల ఆకులపై మచ్చలు లేదా పురుగులు ఉన్నాయేమో చూడండి; వ్యాప్తి కనిపిస్తే వ్యవసాయ అధికారికి తెలియజేయండి.",
    },
    "rec.drain": {
        "en": "Open drainage channels so water does not stand in the field.",
        "hi": "जल निकासी की नालियाँ खोलें ताकि खेत में पानी न रुके।",
        "te": "పొలంలో నీరు నిలవకుండా మురుగు కాలువలు తెరవండి.",
    },
    "rec.follow_shc": {
        "en": "Apply nutrients only as per your Soil Health Card; ask the agriculture officer if unsure.",
        "hi": "पोषक तत्व केवल मृदा स्वास्थ्य कार्ड के अनुसार दें; संदेह हो तो कृषि अधिकारी से पूछें।",
        "te": "పోషకాలను భూసార కార్డు సిఫార్సు ప్రకారమే వేయండి; సందేహం ఉంటే వ్యవసాయ అధికారిని అడగండి.",
    },
    "rec.heat_irrigation": {
        "en": "Plan a light irrigation before the hottest days to reduce heat stress.",
        "hi": "गर्मी का तनाव कम करने के लिए सबसे गर्म दिनों से पहले हल्की सिंचाई की योजना बनाएं।",
        "te": "వేడి ఒత్తిడి తగ్గించడానికి అత్యంత వేడి రోజులకు ముందే తేలికపాటి తడి ఇవ్వండి.",
    },
    "rec.monitor": {
        "en": "Keep monitoring the crop; no urgent action is needed now.",
        "hi": "फसल की निगरानी जारी रखें; अभी किसी तत्काल कार्रवाई की ज़रूरत नहीं है।",
        "te": "పంటను గమనిస్తూ ఉండండి; ప్రస్తుతం అత్యవసర చర్య అవసరం లేదు.",
    },
    # ---- regenerative practices ----------------------------------------------------------------
    "regen.mulch": {
        "en": "Spread crop residue mulch between rows.",
        "hi": "कतारों के बीच फसल अवशेष की मल्चिंग करें।",
        "te": "వరుసల మధ్య పంట అవశేషాలతో మల్చింగ్ చేయండి.",
    },
    "regen.mulch.why": {
        "en": "It keeps moisture in the soil during dry spells and slowly adds organic matter to low-carbon soil.",
        "hi": "यह सूखे में मिट्टी की नमी बचाता है और कम कार्बन वाली मिट्टी में धीरे-धीरे जैविक पदार्थ जोड़ता है।",
        "te": "ఇది వర్షాభావంలో నేల తేమను కాపాడుతుంది, తక్కువ కర్బనం ఉన్న నేలకు క్రమంగా సేంద్రియ పదార్థాన్ని చేరుస్తుంది.",
    },
    "regen.residue_no_burn": {
        "en": "Keep and incorporate crop residue after harvest - do not burn it.",
        "hi": "कटाई के बाद फसल अवशेष खेत में मिलाएं - उन्हें जलाएं नहीं।",
        "te": "కోత తర్వాత పంట అవశేషాలను నేలలో కలపండి - కాల్చవద్దు.",
    },
    "regen.residue_no_burn.why": {
        "en": "Residue builds organic carbon (currently {oc}%) and protects soil moisture for the next crop.",
        "hi": "अवशेष जैविक कार्बन (अभी {oc}%) बढ़ाते हैं और अगली फसल के लिए नमी बचाते हैं।",
        "te": "అవశేషాలు సేంద్రియ కర్బనాన్ని (ప్రస్తుతం {oc}%) పెంచి, తదుపరి పంటకు తేమను కాపాడతాయి.",
    },
    "regen.fym": {
        "en": "Add farmyard manure or compost before the next sowing.",
        "hi": "अगली बुवाई से पहले गोबर की खाद या कम्पोस्ट डालें।",
        "te": "తదుపరి విత్తనానికి ముందు పశువుల ఎరువు లేదా కంపోస్ట్ వేయండి.",
    },
    "regen.fym.why": {
        "en": "Organic carbon is {oc}%, below the 0.5% low threshold; manure improves structure and water holding.",
        "hi": "जैविक कार्बन {oc}% है, 0.5% की सीमा से कम; खाद मिट्टी की संरचना और जल-धारण सुधारती है।",
        "te": "సేంద్రియ కర్బనం {oc}%, 0.5% కనీస స్థాయి కంటే తక్కువ; ఎరువు నేల నిర్మాణం, నీటి నిల్వను మెరుగుపరుస్తుంది.",
    },
    "regen.legume_rotation": {
        "en": "Plan a legume such as chickpea or green gram in the next season.",
        "hi": "अगले मौसम में चना या मूंग जैसी दलहनी फसल की योजना बनाएं।",
        "te": "తదుపరి సీజన్‌లో శనగ లేదా పెసర వంటి పప్పుజాతి పంటను ప్లాన్ చేయండి.",
    },
    "regen.legume_rotation.why": {
        "en": "Legumes fix nitrogen and break pest cycles after {crop}.",
        "hi": "दलहनी फसलें नाइट्रोजन स्थिर करती हैं और {crop} के बाद कीट-चक्र तोड़ती हैं।",
        "te": "పప్పుజాతి పంటలు నత్రజనిని స్థిరీకరిస్తాయి, {crop} తర్వాత పురుగుల చక్రాన్ని విరుస్తాయి.",
    },
    "regen.ridge_furrow": {
        "en": "Use ridges and furrows (or broad beds) and keep grass cover on bunds to manage excess water.",
        "hi": "अतिरिक्त पानी के लिए मेड़-नाली (या चौड़ी क्यारी) अपनाएँ और मेड़ों पर घास रखें।",
        "te": "అదనపు నీటి నిర్వహణకు బోదెలు-కాలువలు (లేదా వెడల్పు మడులు) వాడండి, గట్లపై గడ్డిని ఉంచండి.",
    },
    "regen.ridge_furrow.why": {
        "en": "{rain14} mm rain in 14 days; better drainage protects roots and reduces soil loss.",
        "hi": "14 दिनों में {rain14} मिमी बारिश; बेहतर निकासी जड़ों को बचाती है और मिट्टी का कटाव कम करती है।",
        "te": "14 రోజుల్లో {rain14} మి.మీ. వర్షం; మెరుగైన మురుగు వేర్లను కాపాడి నేల కోతను తగ్గిస్తుంది.",
    },
    "regen.intercrop": {
        "en": "Consider intercropping with red gram next season.",
        "hi": "अगले मौसम में अरहर के साथ अंतरफसल पर विचार करें।",
        "te": "తదుపరి సీజన్‌లో కందితో అంతర పంట వేయడాన్ని పరిశీలించండి.",
    },
    "regen.intercrop.why": {
        "en": "Deep-rooted red gram uses different soil layers and spreads drought risk.",
        "hi": "गहरी जड़ वाली अरहर मिट्टी की अलग परतों का उपयोग करती है और सूखे का जोखिम बाँटती है।",
        "te": "లోతైన వేర్లు గల కంది వేర్వేరు నేల పొరలను వాడుకుని కరువు ప్రమాదాన్ని పంచుతుంది.",
    },
    # ---- timeframes, missing info, freshness ---------------------------------------------------
    "tf.today": {"en": "Today", "hi": "आज", "te": "ఈ రోజు"},
    "tf.48h": {"en": "Next 48 hours", "hi": "अगले 48 घंटे", "te": "రాబోయే 48 గంటలు"},
    "tf.week": {"en": "This week", "hi": "इस सप्ताह", "te": "ఈ వారం"},
    "tf.season": {"en": "This season", "hi": "इस मौसम", "te": "ఈ సీజన్"},
    "miss.no_diagnosis": {
        "en": "No recent crop photo check (Crop Doctor).",
        "hi": "हाल में फसल की फोटो जाँच (क्रॉप डॉक्टर) नहीं हुई।",
        "te": "ఇటీవల పంట ఫోటో పరిశీలన (క్రాప్ డాక్టర్) జరగలేదు.",
    },
    "miss.no_soil_moisture": {
        "en": "No in-field soil moisture measurement.",
        "hi": "खेत में मिट्टी की नमी का मापन उपलब्ध नहीं।",
        "te": "పొలంలో నేల తేమ కొలత అందుబాటులో లేదు.",
    },
    "miss.soil_old": {
        "en": "Soil test is more than a year old.",
        "hi": "मिट्टी की जाँच एक वर्ष से अधिक पुरानी है।",
        "te": "నేల పరీక్ష ఏడాది కంటే పాతది.",
    },
    "fresh.sample": {
        "en": "{category} data is sample/demo data, not a live reading for this field.",
        "hi": "{category} डेटा नमूना/डेमो डेटा है, इस खेत की लाइव रीडिंग नहीं।",
        "te": "{category} డేటా నమూనా/డెమో డేటా, ఈ పొలానికి ప్రత్యక్ష రీడింగ్ కాదు.",
    },
    "fresh.sat_age": {
        "en": "Latest clear satellite image is {days} days old.",
        "hi": "नवीनतम साफ़ उपग्रह चित्र {days} दिन पुराना है।",
        "te": "తాజా స్పష్టమైన ఉపగ్రహ చిత్రం {days} రోజుల క్రితంది.",
    },
    "fresh.soil_date": {"en": "Soil test date: {date}.", "hi": "मिट्टी जाँच की तिथि: {date}।", "te": "నేల పరీక్ష తేదీ: {date}."},
    "cat.weather": {"en": "Weather", "hi": "मौसम", "te": "వాతావరణ"},
    "cat.soil": {"en": "Soil", "hi": "मिट्टी", "te": "నేల"},
    "cat.satellite": {"en": "Satellite", "hi": "उपग्रह", "te": "ఉపగ్రహ"},
    "cat.soil_texture": {"en": "Soil texture", "hi": "मिट्टी की बनावट", "te": "నేల ఆకృతి"},
    "band.Good": {"en": "Good", "hi": "अच्छा", "te": "మంచిది"},
    "band.Moderate": {"en": "Moderate", "hi": "मध्यम", "te": "మధ్యస్థం"},
    "band.Poor": {"en": "Poor", "hi": "कमज़ोर", "te": "బలహీనం"},
    "factor.vegetation": {"en": "vegetation", "hi": "वनस्पति", "te": "పచ్చదనం"},
    "factor.soil": {"en": "soil", "hi": "मिट्टी", "te": "నేల"},
    "factor.weather": {"en": "weather", "hi": "मौसम", "te": "వాతావరణం"},
    "factor.water": {"en": "water", "hi": "पानी", "te": "నీరు"},
    "factor.crop_condition": {"en": "crop condition", "hi": "फसल की स्थिति", "te": "పంట స్థితి"},
    # ---- voice / question answering ------------------------------------------------------------
    "ask.water": {
        "en": "Your field got {rain14} mm of rain in the last 14 days, and {rain3} mm is forecast for the next 3 days. {advice}",
        "hi": "पिछले 14 दिनों में आपके खेत में {rain14} मिमी बारिश हुई और अगले 3 दिनों में {rain3} मिमी का पूर्वानुमान है। {advice}",
        "te": "గత 14 రోజుల్లో మీ పొలంలో {rain14} మి.మీ. వర్షం పడింది, రాబోయే 3 రోజుల్లో {rain3} మి.మీ. సూచన ఉంది. {advice}",
    },
    "ask.disease": {
        "en": "Humidity is {rh}%. {interp} Please upload a leaf photo in Crop Doctor and confirm with the agriculture officer before any spray.",
        "hi": "आर्द्रता {rh}% है। {interp} कृपया क्रॉप डॉक्टर में पत्ते की फोटो डालें और किसी भी छिड़काव से पहले कृषि अधिकारी से पुष्टि करें।",
        "te": "గాలిలో తేమ {rh}%. {interp} దయచేసి క్రాప్ డాక్టర్‌లో ఆకు ఫోటో అప్‌లోడ్ చేసి, ఏ పిచికారీ చేసే ముందైనా వ్యవసాయ అధికారితో నిర్ధారించుకోండి.",
    },
    "ask.fertilizer": {
        "en": "Your soil test shows organic carbon {oc}% and pH {ph}. Apply nutrients as per your Soil Health Card, and add compost or farmyard manure to build organic matter.",
        "hi": "आपकी मिट्टी जाँच में जैविक कार्बन {oc}% और pH {ph} है। मृदा स्वास्थ्य कार्ड के अनुसार पोषक दें और जैविक पदार्थ बढ़ाने के लिए कम्पोस्ट या गोबर खाद डालें।",
        "te": "మీ నేల పరీక్షలో సేంద్రియ కర్బనం {oc}%, pH {ph}. భూసార కార్డు ప్రకారం పోషకాలు వేయండి, సేంద్రియ పదార్థం పెంచేందుకు కంపోస్ట్ లేదా పశువుల ఎరువు వేయండి.",
    },
    "ask.health": {
        "en": "Your Farm Health score is {score} out of 100, which is {band}. The weakest factor is {factor}.",
        "hi": "आपका फार्म हेल्थ स्कोर 100 में से {score} है, जो {band} है। सबसे कमज़ोर कारक {factor} है।",
        "te": "మీ ఫార్మ్ హెల్త్ స్కోరు 100కి {score}, అంటే {band}. అత్యంత బలహీన అంశం {factor}.",
    },
    "ask.sow": {
        "en": "Based on your soil and rainfall, suitable options include {crops}. See Crop Recommendations for the reasons.",
        "hi": "आपकी मिट्टी और बारिश के आधार पर उपयुक्त विकल्प हैं: {crops}। कारण फसल सिफारिश में देखें।",
        "te": "మీ నేల, వర్షపాతం ఆధారంగా అనువైన పంటలు: {crops}. కారణాల కోసం పంట సిఫార్సులు చూడండి.",
    },
    "ask.unknown": {
        "en": "I can answer about rain and irrigation, crop disease, fertiliser, farm health or which crop to sow. Your Farm Health score is {score} out of 100.",
        "hi": "मैं बारिश और सिंचाई, फसल रोग, खाद, फार्म हेल्थ या कौन सी फसल बोएं - इन पर जवाब दे सकता हूँ। आपका फार्म हेल्थ स्कोर 100 में से {score} है।",
        "te": "వర్షం-నీటి తడి, పంట తెగుళ్లు, ఎరువులు, ఫార్మ్ హెల్త్, ఏ పంట వేయాలి అనే విషయాలపై సమాధానం ఇవ్వగలను. మీ ఫార్మ్ హెల్త్ స్కోరు 100కి {score}.",
    },
    "ask.follow_up": {
        "en": "Generate today's advisory for a full plan.",
        "hi": "पूरी योजना के लिए आज की सलाह बनाएं।",
        "te": "పూర్తి ప్రణాళిక కోసం నేటి సలహాను రూపొందించండి.",
    },
}

STAGES: dict[str, dict[str, str]] = {
    "emergence": {"en": "emergence", "hi": "अंकुरण", "te": "మొలక దశ"},
    "establishment": {"en": "establishment", "hi": "स्थापना", "te": "నాటు స్థిరపడే దశ"},
    "vegetative": {"en": "vegetative", "hi": "वानस्पतिक", "te": "శాఖీయ దశ"},
    "tillering": {"en": "tillering", "hi": "कल्ले निकलना", "te": "పిలకల దశ"},
    "flowering": {"en": "flowering", "hi": "फूल आना", "te": "పూత దశ"},
    "flowering_pegging": {"en": "flowering & pegging", "hi": "फूल व खूंटी बनना", "te": "పూత, ఊడల దశ"},
    "flowering_podding": {"en": "flowering & podding", "hi": "फूल व फली बनना", "te": "పూత, కాయ దశ"},
    "pod_development": {"en": "pod development", "hi": "फली विकास", "te": "కాయ అభివృద్ధి దశ"},
    "pod_fill": {"en": "pod filling", "hi": "फली भराव", "te": "కాయ నిండే దశ"},
    "squaring_flowering": {"en": "squaring & flowering", "hi": "कली व फूल", "te": "మొగ్గ, పూత దశ"},
    "boll_development": {"en": "boll development", "hi": "टिंडा विकास", "te": "కాయ (బోల్) అభివృద్ధి దశ"},
    "jointing_booting": {"en": "jointing & booting", "hi": "गाँठ व गभोट", "te": "కణుపు, పొట్ట దశ"},
    "heading_grain_fill": {"en": "heading & grain fill", "hi": "बाली व दाना भराव", "te": "వెన్ను, గింజ నిండే దశ"},
    "grain_fill": {"en": "grain fill", "hi": "दाना भराव", "te": "గింజ నిండే దశ"},
    "tasseling_silking": {"en": "tasseling & silking", "hi": "नर-मादा फूल", "te": "జల్లు, పీచు దశ"},
    "panicle_initiation": {"en": "panicle initiation", "hi": "बाली बनना", "te": "కంకి ఏర్పడే దశ"},
    "maturity": {"en": "maturity", "hi": "परिपक्वता", "te": "పక్వ దశ"},
    "harvested_or_season_complete": {"en": "season complete", "hi": "मौसम पूरा", "te": "సీజన్ పూర్తి"},
    "not_sown": {"en": "not yet sown", "hi": "अभी बुवाई नहीं", "te": "ఇంకా విత్తలేదు"},
    "unknown": {"en": "unknown stage", "hi": "अज्ञात अवस्था", "te": "తెలియని దశ"},
}


def t(code: str, lang: str = "en", **params: Any) -> str:
    table = M[code]
    return table.get(lang, table["en"]).format(**params)


def stage_name(stage: str | None, lang: str = "en") -> str:
    row = STAGES.get(stage or "unknown", STAGES["unknown"])
    return row.get(lang, row["en"])

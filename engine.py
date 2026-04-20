# engine.py

import json
import requests
from typing import Dict, Any, List
from models import PatientHistory


# ---------------- LOAD DATA ----------------
with open("data/fallback_interactions.json") as f:
    FALLBACK_DATA = json.load(f)

with open("prompts/system_prompt.txt") as f:
    SYSTEM_PROMPT = f.read()


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


# ---------------- HELPER ----------------
def _format_drug_name(name: str) -> str:
    return name.strip().title()


# ---------------- MAIN ENGINE ----------------
def check_drug_safety(
    medicines: List[str],
    patient_history: PatientHistory
) -> Dict[str, Any]:

    history_dict = patient_history.dict()

    medicines = list(set(medicines))

    # -------- FALLBACK --------
    result = _fallback_check(medicines, history_dict)
    source = "fallback"

    # -------- LLM (ONLY IF COMPLEX) --------
    if len(medicines) >= 3:
        llm_result = _call_llm(medicines, history_dict)
        if llm_result:
            result = llm_result
            source = "llm"

    # -------- CONDITION CHECK --------
    condition_alerts = _check_condition_contraindications(
        medicines, history_dict.get("conditions", [])
    )
    result["interactions"].extend(condition_alerts)

    # -------- RISK SCORE --------
    result["patient_risk_score"] = _calculate_risk_score(result, history_dict)

    # -------- FINAL DECISION --------
    interactions = result.get("interactions", [])
    allergy_alerts = result.get("allergy_alerts", [])

    has_high = any(i.get("severity") == "high" for i in interactions)
    has_critical_allergy = any(a.get("severity") == "critical" for a in allergy_alerts)

    result["safe_to_prescribe"] = not (has_high or has_critical_allergy)
    result["overall_risk_level"] = "high" if (has_high or has_critical_allergy) else "low"
    result["requires_doctor_review"] = has_high or has_critical_allergy

    result["source"] = source

    return result


# ---------------- LLM ----------------
def _call_llm(medicines, patient_history):

    user_prompt = f"""
Patient Information:
Age: {patient_history.get('age')}
Current medications: {', '.join(patient_history.get('current_medications', []))}
Known allergies: {', '.join(patient_history.get('known_allergies', []))}
Conditions: {', '.join(patient_history.get('conditions', []))}
New medicines: {', '.join(medicines)}

Return ONLY JSON.
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": SYSTEM_PROMPT + user_prompt,
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=3)
        raw = res.json()["response"]
        parsed = _safe_parse_json(raw)

        if parsed:
            parsed = _validate_llm_output(parsed)

        return parsed

    except Exception as e:
        print("LLM Error:", e)
        return None


def _safe_parse_json(text):
    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end]) if start != -1 else None


# ---------------- VALIDATION ----------------
def _validate_llm_output(data: dict) -> dict:

    valid_interactions = []
    for i in data.get("interactions", []):
        if not i.get("drug_a") or not i.get("drug_b"):
            continue

        if i.get("severity") not in ["high", "medium", "low"]:
            i["severity"] = "low"

        if i.get("source_confidence") not in ["high", "medium", "low"]:
            i["source_confidence"] = "low"

        valid_interactions.append(i)

    data["interactions"] = valid_interactions

    valid_alerts = []
    for a in data.get("allergy_alerts", []):
        if not a.get("medicine"):
            continue

        if a.get("severity") not in ["critical", "high", "medium", "low"]:
            a["severity"] = "high"

        valid_alerts.append(a)

    data["allergy_alerts"] = valid_alerts

    return data


# ---------------- FALLBACK ----------------
def _fallback_check(medicines, patient_history):

    meds = [m.lower() for m in medicines]
    interactions = []
    allergy_alerts = []

    allergies = [a.lower() for a in patient_history.get("known_allergies", [])]

    # -------- INTERACTIONS --------
    for rule in FALLBACK_DATA["interactions"]:
        if all(any(d in m for m in meds) for d in rule["drugs"]):
            interactions.append({
                "drug_a": _format_drug_name(rule["drugs"][0]),
                "drug_b": _format_drug_name(rule["drugs"][1]),
                "severity": rule["severity"],
                "mechanism": rule["mechanism"],
                "clinical_recommendation": rule["clinical_recommendation"],
                "source_confidence": rule["source_confidence"]
            })

    # -------- ALLERGY CHECK (FIXED 🔥) --------
    allergy_classes = FALLBACK_DATA.get("allergy_classes", {})

    for allergy in allergies:
        for med in meds:

            # Direct match
            if allergy in med or med in allergy:
                allergy_alerts.append({
                    "medicine": _format_drug_name(med),
                    "reason": f"Direct allergy match: {allergy}",
                    "severity": "critical"
                })

            # Cross-class match
            for class_name, class_drugs in allergy_classes.items():
                if allergy in class_name.lower():
                    for drug in class_drugs:
                        if drug.lower() in med:
                            allergy_alerts.append({
                                "medicine": _format_drug_name(med),
                                "reason": f"Cross-allergy: {class_name}",
                                "severity": "critical"
                            })

    return {
        "interactions": interactions,
        "allergy_alerts": allergy_alerts
    }


# ---------------- CONDITION ----------------
def _check_condition_contraindications(medicines, conditions):

    alerts = []
    data = FALLBACK_DATA.get("condition_contraindications", {})

    for cond in conditions:
        for key, val in data.items():
            if key in cond.lower():
                for med in medicines:
                    if med.lower() in val["drugs"]:
                        alerts.append({
                            "drug_a": _format_drug_name(med),
                            "drug_b": f"[Condition: {cond}]",
                            "severity": val["severity"],
                            "mechanism": val["mechanism"],
                            "clinical_recommendation": val["clinical_recommendation"],
                            "source_confidence": "high"
                        })

    return alerts


# ---------------- RISK ----------------
def _calculate_risk_score(result, history):

    score = 0
    breakdown = []

    for i in result.get("interactions", []):
        if i.get("severity") == "high":
            score += 25
            breakdown.append("high interaction")

    for a in result.get("allergy_alerts", []):
        if a.get("severity") == "critical":
            score += 40
            breakdown.append("critical allergy")

    return {
        "score": min(score, 100),
        "breakdown": " + ".join(breakdown) if breakdown else "low risk"
    }
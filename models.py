# models.py
from pydantic import BaseModel
from typing import List, Optional

class PatientHistory(BaseModel):
    current_medications: List[str] = []
    known_allergies: List[str] = []
    conditions: List[str] = []        # e.g., ["kidney disease", "diabetes"]
    age: Optional[int] = None
    weight: Optional[float] = None

class MedicineRequest(BaseModel):
    medicines: List[str]               # List of proposed medicines
    patient_history: PatientHistory

class DrugInteraction(BaseModel):
    drug_a: str
    drug_b: str
    severity: str                      # "high" / "medium" / "low"
    mechanism: str
    clinical_recommendation: str
    source_confidence: str

class AllergyAlert(BaseModel):
    medicine: str
    reason: str
    severity: str                      # "critical" / "high" / "medium"

class PatientRiskScore(BaseModel):     # Bonus B
    score: int                         # 0-100
    breakdown: str

class SafetyResponse(BaseModel):
    interactions: List[DrugInteraction]
    allergy_alerts: List[AllergyAlert]
    safe_to_prescribe: bool
    overall_risk_level: str
    requires_doctor_review: bool
    source: str                        # "llm" or "fallback"
    cache_hit: bool
    processing_time_ms: int
    patient_risk_score: Optional[PatientRiskScore] = None  # Bonus B
# 🏥 EvoDoc Clinical Drug Safety Engine

A production-ready FastAPI backend system that evaluates drug safety by analyzing:
- Drug-drug interactions
- Allergy risks
- Condition-based contraindications
- Patient-specific risk scoring

Designed to simulate real-world clinical decision support systems used in hospitals.

---

## 🚀 Overview

This system accepts:
- A list of proposed medicines
- A patient's medical history

And returns a **structured safety assessment** including:
- Drug interaction warnings
- Allergy alerts
- Overall risk level
- Prescription safety decision
- Patient risk score

---

## ⚙️ Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Mistral (via Ollama - local inference)
- **Architecture**: Hybrid (Rule-based + LLM)
- **Caching**: In-memory deterministic caching
- **Data Format**: JSON

---

## 🧠 System Architecture
Client Request
↓
FastAPI (main.py)
↓
Validation Layer
↓
Cache Check
↓
Engine (engine.py)
├── Rule-Based Fallback (fast, deterministic)
├── LLM (for complex cases ≥ 3 medicines)
├── Allergy Detection
├── Condition Contraindications
├── Risk Scoring
↓
Response Formatter
↓
JSON Output

---

## 🔥 Key Features

### ✅ Drug Interaction Detection
- Identifies interactions with severity levels:
  - High
  - Medium
  - Low
- Provides mechanism and clinical recommendations

---

### ✅ Patient History Awareness
Considers:
- Current medications
- Known allergies
- Medical conditions
- Age

Ensures all new medicines are cross-checked against patient history.

---

### ✅ Allergy Detection
- Detects direct allergies
- Detects cross-class allergies
- Flags critical risks appropriately

---

### ✅ Condition Contraindications
- Detects unsafe drug usage based on patient conditions
- Example: NSAIDs in kidney disease

---

### ✅ Hybrid AI + Rule-Based System
- **Fallback system** ensures deterministic safety
- **LLM used only for complex cases**
- Prevents reliance on hallucinated outputs

---

### ✅ Smart Caching
- Deterministic cache key (order-independent)
- Avoids recomputation
- Improves response time significantly
- Returns `cache_hit` flag

---

### ✅ Risk Scoring System
- Generates score (0–100)
- Based on:
  - Interaction severity
  - Allergy severity
- Provides breakdown for explainability

---

### ✅ Error Handling (Critical Requirement)
Handles:
- Invalid age (negative values)
- Duplicate medicines
- Empty inputs
- Invalid medicine names

---

## ⚡ Performance Optimization

| Case Type | Response Time |
|----------|--------------|
| Rule-based fallback | ~5–50 ms |
| Cached response | ~1–10 ms |
| LLM-based analysis | < 3 seconds |

---

## 🛡️ Safety & Reliability

- Strict JSON output enforcement
- LLM output validation layer
- No raw LLM text exposed
- Fallback guarantees non-empty responses
- Doctor review flag for high-risk scenarios

---

## 📥 API Endpoint

### POST `/check-interactions`

---

### 📌 Request Example

```json
{
  "medicines": ["Warfarin", "Aspirin"],
  "patient_history": {
    "current_medications": [],
    "known_allergies": ["Penicillin"],
    "conditions": ["kidney disease"],
    "age": 65
  }
}
📌 Response Example
{
  "interactions": [
    {
      "drug_a": "Warfarin",
      "drug_b": "Aspirin",
      "severity": "high",
      "mechanism": "Both inhibit platelet function and increase bleeding risk",
      "clinical_recommendation": "Avoid combination. Monitor INR closely if necessary.",
      "source_confidence": "high"
    }
  ],
  "allergy_alerts": [],
  "safe_to_prescribe": false,
  "overall_risk_level": "high",
  "requires_doctor_review": true,
  "source": "fallback",
  "cache_hit": false,
  "processing_time_ms": 25,
  "patient_risk_score": {
    "score": 25,
    "breakdown": "high interaction"
  }
}
🧪 Running the Project
1. Install dependencies
pip install -r requirements.txt
2. Start FastAPI server
uvicorn main:app --reload
3. Access API docs

Open:

http://localhost:8000/docs
🧠 Design Decisions
🔹 Why Hybrid System?
LLMs are powerful but unreliable for critical healthcare
Rule-based fallback ensures deterministic safety
LLM adds flexibility for complex multi-drug cases
🔹 Why Local LLM (Ollama)?
Ensures patient data privacy
No external API dependency
Suitable for clinical environments
🔹 Why Validation Layer?
Prevents hallucinated outputs
Ensures schema correctness
Guarantees structured responses
⚠️ LLM Choice Note

This implementation uses Mistral via Ollama for local inference.

Due to hardware constraints, a general model is used, but the system is designed to support medical-specific LLMs (BioMistral / Med42 / Meditron) without changes to architecture.

📌 Future Improvements
Expand drug interaction dataset
Integrate real medical knowledge bases (FDA / PubMed)
Improve risk scoring using ML models
Add authentication & logging
Deploy as microservice


👨‍💻 Author

Ayush Bidwai

🏁 Conclusion

This project demonstrates a production-grade clinical safety system combining:

Deterministic rule-based validation
Controlled LLM integration
Robust backend architecture
Strong safety guarantees

Ensuring accuracy, reliability, and performance in critical healthcare scenarios.
# main.py

import time
from fastapi import FastAPI, HTTPException
from models import MedicineRequest, SafetyResponse
from engine import check_drug_safety
from cache import get_cached, set_cache

app = FastAPI(
    title="EvoDoc Clinical Drug Safety Engine",
    description="Checks drug interactions, allergies, and contraindications",
    version="1.0.0"
)


@app.post("/check-interactions", response_model=SafetyResponse)
async def check_interactions(request: MedicineRequest):

    start_time = time.time()

    # -------- VALIDATIONS (EDGE CASES 🔥) --------

    # No medicines
    if not request.medicines:
        raise HTTPException(status_code=400, detail="No medicines provided")

    # Too many medicines
    if len(request.medicines) > 20:
        raise HTTPException(status_code=400, detail="Too many medicines (max 20)")

    # Remove duplicates (case insensitive)
    request.medicines = list(set([m.strip() for m in request.medicines if isinstance(m, str)]))

    # Invalid medicine names
    if not all(isinstance(m, str) and m.strip() for m in request.medicines):
        raise HTTPException(status_code=400, detail="Invalid medicine names")

    # Validate age
    if request.patient_history.age is not None:
        if request.patient_history.age < 0:
            raise HTTPException(status_code=400, detail="Invalid age")

    history_dict = request.patient_history.dict()

    # -------- CACHE CHECK --------
    cached = get_cached(request.medicines, history_dict)

    if cached:
        cached_response = cached.copy()
        cached_response["cache_hit"] = True
        cached_response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return cached_response

    # -------- ENGINE CALL --------
    result = check_drug_safety(request.medicines, request.patient_history)

    # -------- FINAL RESPONSE --------
    result["cache_hit"] = False
    result["processing_time_ms"] = int((time.time() - start_time) * 1000)

    # -------- STORE CACHE (WITHOUT TIME 🔥) --------
    cache_data = result.copy()
    cache_data["processing_time_ms"] = 0
    set_cache(request.medicines, history_dict, cache_data)

    return result


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "EvoDoc Drug Safety Engine"
    }
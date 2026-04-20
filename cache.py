# cache.py
import hashlib
import json
import time
from typing import Optional, Dict, Any

# In-memory cache (Redis optional for bonus)
_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour

def _make_cache_key(medicines: list, patient_history: dict) -> str:
    """
    Cache key must be order-independent for medicines.
    Same drugs in different order = same cache key.
    """
    sorted_meds = sorted([m.lower().strip() for m in medicines])
    sorted_history_meds = sorted([
        m.lower().strip() 
        for m in patient_history.get("current_medications", [])
    ])
    
    key_data = {
        "medicines": sorted_meds,
        "current_medications": sorted_history_meds,
        "allergies": sorted(patient_history.get("known_allergies", [])),
        "conditions": sorted(patient_history.get("conditions", []))
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

def get_cached(medicines: list, patient_history: dict) -> Optional[Dict]:
    key = _make_cache_key(medicines, patient_history)
    entry = _cache.get(key)
    
    if entry is None:
        return None
    
    # Check TTL
    if time.time() - entry["timestamp"] > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    
    return entry["data"]

def set_cache(medicines: list, patient_history: dict, data: Dict) -> None:
    key = _make_cache_key(medicines, patient_history)
    _cache[key] = {
        "data": data,
        "timestamp": time.time()
    }
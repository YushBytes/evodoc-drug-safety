# tests/test_engine.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_warfarin_aspirin_interaction():
    """Classic high-severity interaction must be detected."""
    response = client.post("/check-interactions", json={
        "medicines": ["Warfarin", "Aspirin"],
        "patient_history": {
            "current_medications": [],
            "known_allergies": [],
            "conditions": [],
            "age": 65,
            "weight": 70
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["interactions"]) > 0
    severities = [i["severity"] for i in data["interactions"]]
    assert "high" in severities

def test_penicillin_allergy_cross_reactivity():
    """Patient allergic to Penicillin → Amoxicillin must be flagged."""
    response = client.post("/check-interactions", json={
        "medicines": ["Amoxicillin", "Paracetamol"],
        "patient_history": {
            "current_medications": [],
            "known_allergies": ["Penicillin"],
            "conditions": [],
            "age": 30
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["allergy_alerts"]) > 0
    assert data["safe_to_prescribe"] == False

def test_kidney_disease_nsaid_contraindication():
    """Bonus C: NSAIDs must be flagged for kidney disease."""
    response = client.post("/check-interactions", json={
        "medicines": ["Ibuprofen", "Omeprazole"],
        "patient_history": {
            "current_medications": [],
            "known_allergies": [],
            "conditions": ["kidney disease"],
            "age": 55
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["interactions"]) > 0

def test_cache_works():
    """Second identical request must return cache_hit=True."""
    payload = {
        "medicines": ["Metformin", "Aspirin"],
        "patient_history": {
            "current_medications": [],
            "known_allergies": [],
            "conditions": []
        }
    }
    client.post("/check-interactions", json=payload)  # First call
    response2 = client.post("/check-interactions", json=payload)  # Second call
    assert response2.json()["cache_hit"] == True

def test_response_schema_complete():
    """All required fields must be present."""
    response = client.post("/check-interactions", json={
        "medicines": ["Paracetamol"],
        "patient_history": {
            "current_medications": [],
            "known_allergies": [],
            "conditions": []
        }
    })
    data = response.json()
    required_fields = [
        "interactions", "allergy_alerts", "safe_to_prescribe",
        "overall_risk_level", "requires_doctor_review",
        "source", "cache_hit", "processing_time_ms"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

def test_empty_medicines_rejected():
    """Empty medicine list should return 400."""
    response = client.post("/check-interactions", json={
        "medicines": [],
        "patient_history": {"current_medications": [], "known_allergies": [], "conditions": []}
    })
    assert response.status_code == 400
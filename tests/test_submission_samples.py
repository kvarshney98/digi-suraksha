import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import incidents

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "examples"
CASES = json.loads((SAMPLES / "messages.json").read_text(encoding="utf-8"))

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(incidents, "DB", tmp_path / "sample-tests.sqlite3")
    monkeypatch.delenv("REMOTE_AI_URL", raising=False)
    monkeypatch.delenv("LOCAL_AI_URL", raising=False)
    return TestClient(app)

@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_sample_messages(client, case):
    payload = {key: case[key] for key in ("content", "input_type", "language")}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    assert response.json()["risk"] == case["expected_risk"]
    assert response.json()["provider"] == "deterministic"

def test_sample_email(client):
    response = client.post("/api/analyze/upload", files={"file": ("example.eml", (SAMPLES / "suspicious-email.eml").read_bytes(), "message/rfc822")})
    assert response.status_code == 200
    assert response.json()["risk"] == "High"
    assert {"reply_mismatch", "auth_fail"} <= {item["id"] for item in response.json()["indicators"]}

def test_sample_incident_is_not_saved(client):
    response = client.post("/api/incidents", json=json.loads((SAMPLES / "incident.json").read_text(encoding="utf-8")))
    assert response.status_code == 200
    assert response.json()["id"] is None
    assert "Draft only" in response.json()["guidance"]
    assert client.get("/api/incidents").json() == []

def test_sample_screenshot(client):
    import shutil
    if not shutil.which('tesseract'):
        pytest.skip('Tesseract is required to validate the screenshot sample')
    response = client.post('/api/analyze/upload', files={'file': ('suspicious-screenshot.png', (SAMPLES / 'suspicious-screenshot.png').read_bytes(), 'image/png')})
    assert response.status_code == 200, response.text
    assert response.json()['input_type'] == 'screenshot'
    assert response.json()['risk'] == 'High'

import sys
import os
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

def test_read_settings():
    """
    Test reading the settings.
    """
    response = client.get("/settings/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Should have at least one setting
    
    # Check for a specific setting's structure
    two_step_setting = next((item for item in data if item["name"] == "TwoStepImport"), None)
    assert two_step_setting is not None
    assert "name" in two_step_setting
    assert "value" in two_step_setting
    assert "description" in two_step_setting

def test_update_settings():
    """
    Test updating a setting and reverting it.
    """
    # 1. Get original settings
    response = client.get("/settings/")
    assert response.status_code == 200
    original_settings = response.json()
    two_step_original = next((s for s in original_settings if s['name'] == 'TwoStepImport'), None)
    assert two_step_original is not None
    original_value = two_step_original['value']

    # 2. Prepare and send update
    new_value = "True" if original_value != "True" else "False"
    update_payload = [
        {"name": s["name"], "value": new_value if s["name"] == "TwoStepImport" else s["value"]}
        for s in original_settings
    ]
    response = client.put("/settings/", json=update_payload)
    assert response.status_code == 200

    # 3. Verify update
    response = client.get("/settings/")
    assert response.status_code == 200
    updated_settings = response.json()
    two_step_updated = next((s for s in updated_settings if s['name'] == 'TwoStepImport'), None)
    assert two_step_updated is not None
    assert two_step_updated['value'] == new_value

    # 4. Prepare and send revert
    revert_payload = [
        {"name": s["name"], "value": original_value if s["name"] == "TwoStepImport" else s["value"]}
        for s in updated_settings
    ]
    response = client.put("/settings/", json=revert_payload)
    assert response.status_code == 200

    # 5. Verify revert
    response = client.get("/settings/")
    assert response.status_code == 200
    final_settings = response.json()
    two_step_final = next((s for s in final_settings if s['name'] == 'TwoStepImport'), None)
    assert two_step_final is not None
    assert two_step_final['value'] == original_value
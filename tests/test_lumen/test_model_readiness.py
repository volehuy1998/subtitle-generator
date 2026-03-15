"""Phase Lumen L3 — Model readiness tests.

Tests the model status API endpoint and readiness reporting.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


class TestModelStatusEndpoint:
    """Test /api/model-status endpoint."""

    def test_model_status_returns_200(self):
        res = client.get("/api/model-status")
        assert res.status_code == 200

    def test_model_status_has_preload_key(self):
        res = client.get("/api/model-status")
        data = res.json()
        assert "preload" in data

    def test_model_status_has_models_key(self):
        res = client.get("/api/model-status")
        data = res.json()
        assert "models" in data

    def test_all_model_sizes_present(self):
        """All 5 model sizes should be in the response."""
        res = client.get("/api/model-status")
        models = res.json()["models"]
        for size in ["tiny", "base", "small", "medium", "large"]:
            assert size in models, f"Model '{size}' missing from readiness response"

    def test_model_status_fields(self):
        """Each model should have status, size_gb, and loaded_devices."""
        res = client.get("/api/model-status")
        models = res.json()["models"]
        for name, info in models.items():
            assert "status" in info, f"Model '{name}' missing 'status'"
            assert "size_gb" in info, f"Model '{name}' missing 'size_gb'"
            assert "loaded_devices" in info, f"Model '{name}' missing 'loaded_devices'"

    def test_model_status_valid_values(self):
        """Status should be one of: ready, loading, not_loaded."""
        res = client.get("/api/model-status")
        models = res.json()["models"]
        valid_statuses = {"ready", "loading", "not_loaded"}
        for name, info in models.items():
            assert info["status"] in valid_statuses, f"Model '{name}' has invalid status: {info['status']}"

    def test_model_size_values(self):
        """Model sizes should be reasonable numbers."""
        res = client.get("/api/model-status")
        models = res.json()["models"]
        expected_sizes = {"tiny": 0.5, "base": 0.8, "small": 1.5, "medium": 3.0, "large": 5.5}
        for name, expected in expected_sizes.items():
            assert models[name]["size_gb"] == expected, f"Model '{name}' size mismatch"


class TestModelPreloadStatus:
    """Test the preload information in model status."""

    def test_preload_has_status(self):
        res = client.get("/api/model-status")
        preload = res.json()["preload"]
        assert "status" in preload

    def test_preload_status_is_valid(self):
        res = client.get("/api/model-status")
        preload = res.json()["preload"]
        assert preload["status"] in {"idle", "loading", "ready", "error"}

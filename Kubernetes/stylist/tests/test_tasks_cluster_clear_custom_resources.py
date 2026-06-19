import sys
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
import kubernetes_asyncio

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.tasks.cluster.ClearCustomResources import ClearCustomResources  # noqa: E402


class MockCRD:
    """Mock CRD object for testing."""
    def __init__(self, name: str, deletion_timestamp: datetime | None = None):
        self.metadata = MagicMock()
        self.metadata.name = name
        self.metadata.deletion_timestamp = deletion_timestamp


class MockCRDList:
    """Mock CRD list response."""
    def __init__(self, items: list[MockCRD]):
        self.items = items


class MockApiClient:
    """Mock Kubernetes API client context manager."""
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockApiextensionsV1Api:
    """Mock ApiextensionsV1Api for testing."""
    def __init__(self, crds: list[MockCRD] | None = None):
        self.crds = crds or []
        self.patch_calls = []
        self.delete_calls = []

    async def list_custom_resource_definition(self):
        return MockCRDList(self.crds)

    async def patch_custom_resource_definition(self, name: str, body: dict):
        self.patch_calls.append((name, body))
        return MagicMock()

    async def delete_custom_resource_definition(self, name: str, body):
        self.delete_calls.append((name, body))
        return MagicMock()


@pytest.fixture
def mock_api_client(monkeypatch):
    """Fixture to mock Kubernetes API client."""
    def create_mock_client():
        return MockApiClient()
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_mock_client)
    return create_mock_client


@pytest.mark.asyncio
async def test_clear_custom_resources_success_no_crds(monkeypatch):
    """Test that ClearCustomResources succeeds when there are no CRDs."""
    task = ClearCustomResources()

    async def mock_delete_all():
        pass

    async def mock_wait_for_terminations(timeout):
        return True, []

    monkeypatch.setattr("stylist.helpers.cluster.delete_all_custom_resources", mock_delete_all)
    monkeypatch.setattr("stylist.helpers.cluster.wait_for_crd_terminations", mock_wait_for_terminations)

    result = await task.run()
    assert result is True


@pytest.mark.asyncio
async def test_clear_custom_resources_success_after_cleanup(monkeypatch):
    """Test that ClearCustomResources succeeds after force cleanup."""
    task = ClearCustomResources()
    call_count = {"delete": 0, "wait": 0, "force_delete": 0, "force_remove": 0, "force_delete_crd": 0}

    async def mock_delete_all():
        call_count["delete"] += 1

    async def mock_wait_for_terminations(timeout):
        call_count["wait"] += 1
        if call_count["wait"] == 1:
            # First call: CRDs still terminating
            return False, ["crd1", "crd2"]
        # Second call: all cleared
        return True, []

    async def mock_force_delete_custom_resources(crd_names):
        call_count["force_delete"] += 1
        assert crd_names == ["crd1", "crd2"]

    async def mock_force_remove_crd_finalizers(crd_names, logger=None):
        call_count["force_remove"] += 1
        assert crd_names == ["crd1", "crd2"]
        return True

    async def mock_force_delete_crd(crd_name, logger=None):
        call_count["force_delete_crd"] += 1
        return True

    monkeypatch.setattr("stylist.helpers.cluster.delete_all_custom_resources", mock_delete_all)
    monkeypatch.setattr("stylist.helpers.cluster.wait_for_crd_terminations", mock_wait_for_terminations)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_custom_resources", mock_force_delete_custom_resources)
    monkeypatch.setattr("stylist.helpers.cluster.force_remove_crd_finalizers", mock_force_remove_crd_finalizers)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_crd", mock_force_delete_crd)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())  # Mock sleep to speed up tests

    result = await task.run()

    assert result is True
    # delete_all is called once per attempt, and we have 2 attempts (first fails, second succeeds)
    assert call_count["delete"] == 2
    assert call_count["wait"] == 2
    assert call_count["force_delete"] == 1
    assert call_count["force_remove"] == 1
    assert call_count["force_delete_crd"] == 2  # One for each CRD


@pytest.mark.asyncio
async def test_clear_custom_resources_retries_on_failure(monkeypatch):
    """Test that ClearCustomResources retries up to 3 times."""
    task = ClearCustomResources()
    call_count = {"wait": 0}

    async def mock_delete_all():
        pass

    async def mock_wait_for_terminations(timeout):
        call_count["wait"] += 1
        # Always return terminating CRDs
        return False, ["stuck-crd"]

    async def mock_force_delete_custom_resources(crd_names):
        pass

    async def mock_force_remove_crd_finalizers(crd_names, logger=None):
        return True

    async def mock_force_delete_crd(crd_name, logger=None):
        return True

    monkeypatch.setattr("stylist.helpers.cluster.delete_all_custom_resources", mock_delete_all)
    monkeypatch.setattr("stylist.helpers.cluster.wait_for_crd_terminations", mock_wait_for_terminations)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_custom_resources", mock_force_delete_custom_resources)
    monkeypatch.setattr("stylist.helpers.cluster.force_remove_crd_finalizers", mock_force_remove_crd_finalizers)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_crd", mock_force_delete_crd)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    result = await task.run()

    assert result is False  # Should fail after 3 attempts
    assert call_count["wait"] == 3  # Should have tried 3 times


@pytest.mark.asyncio
async def test_clear_custom_resources_logs_warnings(monkeypatch):
    """Test that ClearCustomResources logs warnings when CRDs are stuck."""
    task = ClearCustomResources()

    async def mock_delete_all():
        pass

    async def mock_wait_for_terminations(timeout):
        return False, ["crd1", "crd2"]

    async def mock_force_delete_custom_resources(crd_names):
        pass

    async def mock_force_remove_crd_finalizers(crd_names, logger=None):
        return True

    async def mock_force_delete_crd(crd_name, logger=None):
        return True

    monkeypatch.setattr("stylist.helpers.cluster.delete_all_custom_resources", mock_delete_all)
    monkeypatch.setattr("stylist.helpers.cluster.wait_for_crd_terminations", mock_wait_for_terminations)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_custom_resources", mock_force_delete_custom_resources)
    monkeypatch.setattr("stylist.helpers.cluster.force_remove_crd_finalizers", mock_force_remove_crd_finalizers)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_crd", mock_force_delete_crd)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    await task.run()

    # Check that warnings were logged in the log_recorder
    warning_logs = [
        record.getMessage() for record in task.log_recorder.get_all()
        if record.levelname == "WARNING"
    ]
    assert any("CRDs still terminating" in msg for msg in warning_logs)
    assert any("crd1" in msg and "crd2" in msg for msg in warning_logs)


@pytest.mark.asyncio
async def test_clear_custom_resources_logs_error_on_final_failure(monkeypatch):
    """Test that ClearCustomResources logs error when all retries fail."""
    task = ClearCustomResources()

    async def mock_delete_all():
        pass

    async def mock_wait_for_terminations(timeout):
        return False, ["final-stuck-crd"]

    async def mock_force_delete_custom_resources(crd_names):
        pass

    async def mock_force_remove_crd_finalizers(crd_names, logger=None):
        return True

    async def mock_force_delete_crd(crd_name, logger=None):
        return True

    monkeypatch.setattr("stylist.helpers.cluster.delete_all_custom_resources", mock_delete_all)
    monkeypatch.setattr("stylist.helpers.cluster.wait_for_crd_terminations", mock_wait_for_terminations)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_custom_resources", mock_force_delete_custom_resources)
    monkeypatch.setattr("stylist.helpers.cluster.force_remove_crd_finalizers", mock_force_remove_crd_finalizers)
    monkeypatch.setattr("stylist.helpers.cluster.force_delete_crd", mock_force_delete_crd)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    result = await task.run()

    assert result is False
    # Check that errors were logged in the log_recorder
    error_logs = [
        record.getMessage() for record in task.log_recorder.get_all()
        if record.levelname == "ERROR"
    ]
    assert any("Failed to remove CRDs after forced cleanup" in msg for msg in error_logs)
    assert any("final-stuck-crd" in msg for msg in error_logs)

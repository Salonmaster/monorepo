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

from stylist.helpers import cluster  # noqa: E402


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
    def __init__(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_wait_for_crd_terminations_no_terminating(monkeypatch):
    """Test wait_for_crd_terminations when no CRDs are terminating."""
    mock_api = MagicMock()
    mock_api.list_custom_resource_definition = AsyncMock(
        return_value=MockCRDList([
            MockCRD("crd1", None),
            MockCRD("crd2", None),
        ])
    )

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    cleared, remaining = await cluster.wait_for_crd_terminations(timeout=1)

    assert cleared is True
    assert remaining == []


@pytest.mark.asyncio
async def test_wait_for_crd_terminations_with_terminating(monkeypatch):
    """Test wait_for_crd_terminations when CRDs are terminating."""
    mock_api = MagicMock()
    deletion_time = datetime.now()
    call_count = {"list": 0}

    async def mock_list():
        call_count["list"] += 1
        if call_count["list"] == 1:
            # First call: CRDs still terminating
            return MockCRDList([
                MockCRD("crd1", deletion_time),
                MockCRD("crd2", None),
            ])
        # Second call: all cleared
        return MockCRDList([
            MockCRD("crd1", None),
            MockCRD("crd2", None),
        ])

    mock_api.list_custom_resource_definition = AsyncMock(side_effect=mock_list)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    cleared, remaining = await cluster.wait_for_crd_terminations(timeout=10)

    assert cleared is True
    assert remaining == []


@pytest.mark.asyncio
async def test_wait_for_crd_terminations_timeout(monkeypatch):
    """Test wait_for_crd_terminations times out when CRDs remain terminating."""
    mock_api = MagicMock()
    deletion_time = datetime.now()

    async def mock_list():
        return MockCRDList([
            MockCRD("stuck-crd1", deletion_time),
            MockCRD("stuck-crd2", deletion_time),
        ])

    mock_api.list_custom_resource_definition = AsyncMock(side_effect=mock_list)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)

    # Mock time to make timeout happen quickly
    original_time = time.time
    start_time = original_time()
    time_calls = [start_time]

    def mock_time():
        if len(time_calls) == 1:
            time_calls.append(start_time)
        else:
            # Simulate timeout after 2 calls
            time_calls.append(start_time + 2)  # Exceeds timeout of 1
        return time_calls[-1]

    monkeypatch.setattr(time, "time", mock_time)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    cleared, remaining = await cluster.wait_for_crd_terminations(timeout=1)

    assert cleared is False
    assert set(remaining) == {"stuck-crd1", "stuck-crd2"}


@pytest.mark.asyncio
async def test_force_remove_crd_finalizers_success(monkeypatch):
    """Test force_remove_crd_finalizers successfully removes finalizers."""
    mock_api = MagicMock()
    patch_calls = []

    async def mock_patch(name, body):
        patch_calls.append((name, body))
        return MagicMock()

    mock_api.patch_custom_resource_definition = AsyncMock(side_effect=mock_patch)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr("typer.secho", MagicMock())  # Mock typer output

    result = await cluster.force_remove_crd_finalizers(["crd1", "crd2"])

    assert result is True
    assert len(patch_calls) == 2
    assert patch_calls[0][0] == "crd1"
    assert patch_calls[0][1] == {"metadata": {"finalizers": []}}
    assert patch_calls[1][0] == "crd2"
    assert patch_calls[1][1] == {"metadata": {"finalizers": []}}


@pytest.mark.asyncio
async def test_force_remove_crd_finalizers_empty_list(monkeypatch):
    """Test force_remove_crd_finalizers with empty list."""
    result = await cluster.force_remove_crd_finalizers([])
    assert result is True


@pytest.mark.asyncio
async def test_force_remove_crd_finalizers_handles_exception(monkeypatch):
    """Test force_remove_crd_finalizers handles exceptions gracefully."""
    mock_api = MagicMock()

    async def mock_patch(name, body):
        if name == "crd1":
            raise Exception("API error")
        return MagicMock()

    mock_api.patch_custom_resource_definition = AsyncMock(side_effect=mock_patch)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr("typer.secho", MagicMock())

    result = await cluster.force_remove_crd_finalizers(["crd1", "crd2"])

    assert result is False  # Should return False due to exception


@pytest.mark.asyncio
async def test_force_delete_crd_success(monkeypatch):
    """Test force_delete_crd successfully deletes a CRD."""
    mock_api = MagicMock()
    patch_calls = []
    delete_calls = []
    read_calls = []

    # Mock CRD with finalizers
    mock_crd = MagicMock()
    mock_crd.metadata.finalizers = ["finalizer1"]

    async def mock_read(name):
        read_calls.append(name)
        if len(read_calls) == 1:
            # First read: CRD exists with finalizers
            return mock_crd
        # Subsequent reads: CRD deleted (404)
        from kubernetes_asyncio.client.rest import ApiException
        exc = ApiException(status=404)
        raise exc

    async def mock_patch(name, body):
        patch_calls.append((name, body))
        return MagicMock()

    async def mock_delete(name, body):
        delete_calls.append((name, body))
        return MagicMock()

    mock_api.read_custom_resource_definition = AsyncMock(side_effect=mock_read)
    mock_api.patch_custom_resource_definition = AsyncMock(side_effect=mock_patch)
    mock_api.delete_custom_resource_definition = AsyncMock(side_effect=mock_delete)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    # Mock kubectl subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    async def mock_create_subprocess_exec(*args, **kwargs):
        return mock_process

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_subprocess_exec)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.setattr("typer.secho", MagicMock())

    result = await cluster.force_delete_crd("test-crd")

    assert result is True
    assert len(patch_calls) == 1
    assert patch_calls[0][0] == "test-crd"
    assert len(delete_calls) == 1
    assert delete_calls[0][0] == "test-crd"
    assert delete_calls[0][1].grace_period_seconds == 0


@pytest.mark.asyncio
async def test_force_delete_crd_handles_404(monkeypatch):
    """Test force_delete_crd handles 404 (already deleted) gracefully."""
    mock_api = MagicMock()
    from kubernetes_asyncio.client.rest import ApiException

    async def mock_read(name):
        # CRD doesn't exist (404)
        exc = ApiException(status=404)
        raise exc

    async def mock_patch(name, body):
        return MagicMock()

    async def mock_delete(name, body):
        exc = ApiException(status=404)
        raise exc

    mock_api.read_custom_resource_definition = AsyncMock(side_effect=mock_read)
    mock_api.patch_custom_resource_definition = AsyncMock(side_effect=mock_patch)
    mock_api.delete_custom_resource_definition = AsyncMock(side_effect=mock_delete)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    # Mock kubectl subprocess
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    async def mock_create_subprocess_exec(*args, **kwargs):
        return mock_process

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_subprocess_exec)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.setattr("typer.secho", MagicMock())

    result = await cluster.force_delete_crd("test-crd")

    assert result is True  # 404 is treated as success (already deleted)


@pytest.mark.asyncio
async def test_force_delete_crd_handles_other_errors(monkeypatch):
    """Test force_delete_crd handles non-404 errors."""
    mock_api = MagicMock()
    from kubernetes_asyncio.client.rest import ApiException

    # Mock CRD with finalizers
    mock_crd = MagicMock()
    mock_crd.metadata.finalizers = ["finalizer1"]

    async def mock_read(name):
        return mock_crd

    async def mock_patch(name, body):
        return MagicMock()

    async def mock_delete(name, body):
        exc = ApiException(status=500)
        raise exc

    mock_api.read_custom_resource_definition = AsyncMock(side_effect=mock_read)
    mock_api.patch_custom_resource_definition = AsyncMock(side_effect=mock_patch)
    mock_api.delete_custom_resource_definition = AsyncMock(side_effect=mock_delete)

    def create_api_client():
        return MockApiClient()

    def create_api(api_client):
        return mock_api

    # Mock kubectl subprocess to raise an exception (simulating kubectl failure)
    async def mock_create_subprocess_exec(*args, **kwargs):
        raise Exception("kubectl not found")

    monkeypatch.setattr(kubernetes_asyncio.client, "ApiClient", create_api_client)
    monkeypatch.setattr(kubernetes_asyncio.client, "ApiextensionsV1Api", create_api)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_subprocess_exec)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.setattr("typer.secho", MagicMock())

    result = await cluster.force_delete_crd("test-crd")

    # Should return False because API delete raises 500 error
    assert result is False

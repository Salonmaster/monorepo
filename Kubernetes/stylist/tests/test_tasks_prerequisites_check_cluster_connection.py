import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.tasks.prerequisites.CheckClusterConnection import CheckClusterConnection  # noqa: E402


@pytest.mark.asyncio
async def test_check_cluster_connection_success(monkeypatch):
    """Test CheckClusterConnection succeeds when cluster is reachable."""
    task = CheckClusterConnection()

    async def mock_check():
        return True

    monkeypatch.setattr("stylist.helpers.cluster.check_cluster_connection", mock_check)

    result = await task.run()
    assert result is True


@pytest.mark.asyncio
async def test_check_cluster_connection_failure(monkeypatch):
    """Test CheckClusterConnection fails when cluster is not reachable."""
    task = CheckClusterConnection()

    async def mock_check():
        return False

    monkeypatch.setattr("stylist.helpers.cluster.check_cluster_connection", mock_check)

    result = await task.run()
    assert result is False

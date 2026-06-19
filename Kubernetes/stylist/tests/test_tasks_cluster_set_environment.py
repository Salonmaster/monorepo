import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.tasks.cluster.SetEnvironmentTask import SetEnvironmentTask  # noqa: E402
from stylist.enums.environment import Environment  # noqa: E402


@pytest.mark.asyncio
async def test_set_environment_task_sets_environment(monkeypatch):
    """Test SetEnvironmentTask sets environment when different."""
    task = SetEnvironmentTask(Environment.TST)

    async def mock_fetch():
        return None  # No environment set

    async def mock_set(env):
        return True

    monkeypatch.setattr("stylist.helpers.cluster.fetch_cluster_environment", mock_fetch)
    monkeypatch.setattr("stylist.helpers.cluster.set_cluster_environment", mock_set)

    result = await task.run()
    assert result is True


@pytest.mark.asyncio
async def test_set_environment_task_skips_when_already_set(monkeypatch):
    """Test SetEnvironmentTask skips when environment already matches."""
    task = SetEnvironmentTask(Environment.TST)

    async def mock_fetch():
        return Environment.TST  # Already set

    monkeypatch.setattr("stylist.helpers.cluster.fetch_cluster_environment", mock_fetch)

    result = await task.run()
    assert result is True


@pytest.mark.asyncio
async def test_set_environment_task_resets_when_none(monkeypatch):
    """Test SetEnvironmentTask resets environment when None is passed."""
    task = SetEnvironmentTask(None)

    async def mock_fetch():
        return Environment.TST  # Currently set

    async def mock_set(env):
        assert env is None
        return True

    monkeypatch.setattr("stylist.helpers.cluster.fetch_cluster_environment", mock_fetch)
    monkeypatch.setattr("stylist.helpers.cluster.set_cluster_environment", mock_set)

    result = await task.run()
    assert result is True

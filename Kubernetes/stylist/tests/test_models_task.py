import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import asyncio
from stylist.models.task import Task
from stylist.enums.task_status import TaskStatus


class MockTask(Task):
    """Mock task for testing."""
    async def run(self) -> bool:
        return True


def test_task_initialization():
    """Test Task initialization."""
    task = MockTask(name="test-task")
    assert task.name == "test-task"
    assert task.status == TaskStatus.INITIALIZING
    assert task.delay == 0
    assert task.retries == 5
    assert task.backoff == 0
    assert task.current_attempt == 1
    assert task.started is None
    assert task.finished is None
    assert len(task.dependencies) == 0
    assert task.uuid is not None
    assert task.logger is not None
    assert task.log_recorder is not None
    assert task.completed is not None


def test_task_run_not_implemented():
    """Test that base Task.run() raises NotImplementedError."""
    task = Task(name="base-task")

    with pytest.raises(NotImplementedError):
        asyncio.run(task.run())


def test_task_logger_setup():
    """Test that Task sets up logger correctly."""
    task = MockTask(name="test-logger")
    assert task.logger.name.startswith("stylist.models.task.task.test-logger")
    assert task.logger.level == 10  # DEBUG level
    assert len(task.logger.handlers) > 0


def test_task_with_dependencies():
    """Test Task with dependencies."""
    dep1 = MockTask(name="dep1")
    dep2 = MockTask(name="dep2")
    task = MockTask(name="main", dependencies=[dep1, dep2])

    assert len(task.dependencies) == 2
    assert dep1 in task.dependencies
    assert dep2 in task.dependencies

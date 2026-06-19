from __future__ import annotations

import asyncio
import logging
from typing import Callable, TYPE_CHECKING, Optional

import enums

from .task_runner import TaskRunner

if TYPE_CHECKING:
    from models import Task


LogHandler = Callable[["Task", logging.LogRecord, str], None]

class TaskOrchestrator:
    def __init__(self, tasks: Optional[list[Task]] = None):
        self.tasks: list[Task] = tasks if tasks is not None else []
        self._runners: list[TaskRunner] = []
        self._running: bool = False
        self._asyncio_tasks: list[asyncio.Task] = []

    async def run(self):
        # Create a list of TaskRunners for each task
        self._runners = [TaskRunner(task) for task in self.tasks]
        self._asyncio_tasks = []
        self._set_dependencies()

    def process_tasks(self) -> bool:
        for runner in self._runners:
            match(runner.task.status):
                # Start tasks without dependencies first
                case enums.TaskStatus.INITIALIZING:
                    if len(runner.task.dependencies) == 0:
                        self._asyncio_tasks.append(asyncio.create_task(runner.run()))
                    else:
                        runner.task.status = enums.TaskStatus.WAITING
                case enums.TaskStatus.WAITING:
                    if len(runner.dependencies_blocking()) == 0:
                        runner.task.status = enums.TaskStatus.UP_NEXT
                # Start tasks that are ready to run
                case enums.TaskStatus.UP_NEXT:
                    if len(runner.dependencies_blocking()) == 0:
                        self._asyncio_tasks.append(asyncio.create_task(runner.run()))
                case enums.TaskStatus.RUNNING:
                    if len(runner.dependencies_failed()) > 0:
                        runner.task.status = enums.TaskStatus.FAILED
                case enums.TaskStatus.FAILED:
                    if runner.task.current_attempt < runner.task.retries:
                        runner.task.current_attempt += 1
                        runner.task.status = enums.TaskStatus.RETRYING
                        runner.task.backoff = 2 ** runner.task.current_attempt
                        self._asyncio_tasks.append(asyncio.create_task(runner.run()))
                    else:
                        for async_task in self._asyncio_tasks:
                            async_task.cancel()
                            return False

        return any(runner.task.status not in (enums.TaskStatus.SUCCEEDED, enums.TaskStatus.SUCCEEDED_WITH_WARNINGS) for runner in self._runners)

    def _set_dependencies(self):
        for runner in self._runners:
            dependant_tasks = []
            if runner.task.dependencies:
                for task_dependency in runner.task.dependencies:
                    for dependant_runner in self._runners:
                        if isinstance(dependant_runner.task, task_dependency):
                            dependant_tasks.append(dependant_runner.task)
                runner.set_dependant_tasks(dependant_tasks)

    def _tasks_completed_successfully(self) -> bool:
        return all(
            task.status in (enums.TaskStatus.SUCCEEDED, enums.TaskStatus.SUCCEEDED_WITH_WARNINGS)
            for task in self.tasks
        )

    def _emit_new_logs(self, log_handler: LogHandler | None, last_seen: dict[str, int]) -> None:
        if not log_handler:
            return

        for runner in self._runners:
            task = runner.task
            records = task.log_recorder.get_all()
            start_index = last_seen.get(task.uuid, 0)
            if start_index > len(records):
                start_index = len(records)
            new_records = records[start_index:]
            if not new_records:
                continue
            for record in new_records:
                formatted = task.log_recorder.format(record)
                log_handler(task, record, formatted)
            last_seen[task.uuid] = len(records)

    async def _run_headless(self, log_handler: LogHandler | None, poll_interval: float) -> bool:
        await self.run()
        last_seen: dict[str, int] = {runner.task.uuid: 0 for runner in self._runners}

        while True:
            self._emit_new_logs(log_handler, last_seen)
            has_more = self.process_tasks()
            if not has_more:
                break
            await asyncio.sleep(poll_interval)

        if self._asyncio_tasks:
            await asyncio.gather(*self._asyncio_tasks, return_exceptions=True)
        self._emit_new_logs(log_handler, last_seen)
        return self._tasks_completed_successfully()

    def run_cli(self, log_handler: LogHandler | None = None, poll_interval: float = 0.2) -> bool:
        return asyncio.run(self._run_headless(log_handler, poll_interval))

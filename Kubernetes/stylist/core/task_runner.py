import enums
import models
import logging
import asyncio
import datetime

class TaskRunner:
    def __init__(self, task: models.Task):
        self.task = task

    _dependant_tasks = []

    def set_dependant_tasks(self, tasks: list[models.Task]):
        self._dependant_tasks = tasks

    def dependencies_failed(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.FAILED]

    def dependencies_running(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.RUNNING]

    def dependencies_queued(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.QUEUED]

    def dependencies_retrying(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.RETRYING]

    def dependencies_up_next(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.UP_NEXT]

    def dependencies_initializing(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.INITIALIZING]

    def dependencies_waiting(self) -> list[models.Task]:
        return [dep for dep in self._dependant_tasks if dep.status == enums.TaskStatus.WAITING]

    def dependencies_blocking(self) -> list[models.Task]:
        return (
            self.dependencies_failed()
            + self.dependencies_queued()
            + self.dependencies_waiting()
            + self.dependencies_running()
            + self.dependencies_up_next()
            + self.dependencies_retrying()
            + self.dependencies_initializing()
        )

    async def run(self):
        # Delay task if needed
        while self.task.delay > 0:
            if self.task.status != enums.TaskStatus.QUEUED:
                self.task.logger.info(f"Delaying task by {self.task.delay} seconds")
                self.task.status = enums.TaskStatus.QUEUED
            self.task.delay -= 1
            await asyncio.sleep(1)

        # Wait for retry backoff too
        while self.task.backoff > 0:
            self.task.backoff -= 1
            await asyncio.sleep(1)

        # Run task
        self.task.status = enums.TaskStatus.RUNNING
        self.task.started = datetime.datetime.now()
        try:
            if await self.task.run():

                if any(log.levelno == logging.WARNING for log in self.task.log_recorder.get_all()):
                    self.task.logger.warning("Task succeeded with warnings")
                    self.task.status = enums.TaskStatus.SUCCEEDED_WITH_WARNINGS
                else:
                    self.task.logger.info("Task succeeded")
                    self.task.status = enums.TaskStatus.SUCCEEDED
            else:
                self.task.status = enums.TaskStatus.FAILED
        except Exception as e:
            self.task.status = enums.TaskStatus.FAILED
            self.task.logger.info(f"Task failed: {e}")
        finally:
            self.task.finished = datetime.datetime.now()

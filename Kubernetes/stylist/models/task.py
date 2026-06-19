from __future__ import annotations
import uuid
import logging
import asyncio
import datetime
from dataclasses import dataclass, field
from enums import TaskStatus
from core.log_recorder import LogRecorder
@dataclass
class Task:
    name: str
    status: TaskStatus = TaskStatus.INITIALIZING
    delay: int = 0
    retries: int = 5
    backoff: int = 0
    current_attempt: int = 1
    started: datetime.datetime | None = None
    finished: datetime.datetime | None = None
    dependencies: list["Task"] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))

    logger: logging.Logger = field(init=False, repr=False)
    log_recorder: LogRecorder = field(default_factory=LogRecorder, repr=False)

    # NEW: completed event
    completed: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.task.{self.name}_{self.uuid}")
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

        if not any(isinstance(h, LogRecorder) for h in self.logger.handlers):
            if self.log_recorder.formatter is None:
                self.log_recorder.setFormatter(logging.Formatter(
                    "%(asctime)s %(levelname)s %(name)s: %(message)s"
                ))
            self.logger.addHandler(self.log_recorder)

    async def run(self) -> bool:
        raise NotImplementedError

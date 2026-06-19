import logging
from collections import deque
from threading import RLock

class LogRecorder(logging.Handler):
    """In-memory ring buffer for recent log records."""
    def __init__(self, max_records=1000, formatter=None):
        super().__init__(level=logging.NOTSET)  # don't filter here
        self._records = deque(maxlen=max_records)
        self._lock = RLock()
        if formatter is not None:
            self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(record)

    def get_all(self, reverse: bool = False) -> list[logging.LogRecord]:
        """Get all log records as a list."""
        with self._lock:
            return list(reversed(self._records)) if reverse else list(self._records)

    def get_last(self, formatted: bool = True) -> str | logging.LogRecord | None:
        if not self._records:
            return None
        rec = self._records[-1]
        return self.format(rec) if formatted else rec

    def get_messages(self):
        return [self.format(r) for r in self._records]

    def clear(self):
        self._records.clear()

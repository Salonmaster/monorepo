from enum import Enum

class TaskStatus(str, Enum):
    INITIALIZING = "initializing"
    QUEUED = "queued"
    WAITING = "waiting"
    UP_NEXT = "up next"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "partial success"
    FAILED = "failed"


TaskStatusStyles = {
    TaskStatus.INITIALIZING: "cyan",       # Neutral, starting up
    TaskStatus.QUEUED: "bright_black",     # Dim/grey, waiting in line
    TaskStatus.WAITING: "yellow",          # Caution, idle but ready
    TaskStatus.UP_NEXT: "purple",         # Up next, preparing to run
    TaskStatus.RUNNING: "blue",            # Active, in progress
    TaskStatus.RETRYING: "magenta",        # Retrying, attempting again
    TaskStatus.SUCCEEDED: "green",               # Success
    TaskStatus.SUCCEEDED_WITH_WARNINGS: "yellow", # Success with warnings
    TaskStatus.FAILED: "red",               # Error
}

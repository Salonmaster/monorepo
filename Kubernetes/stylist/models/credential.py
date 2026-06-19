from dataclasses import dataclass, field
from typing import Any, Dict
import uuid

@dataclass
class Credential:
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="")
    fields: Dict[str, Any] = field(default_factory=dict)

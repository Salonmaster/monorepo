
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class VaultSecret:
    """Representation of a Vault secret."""

    namespace: str
    name: str
    key: str
    value: Optional[str] = None
    environment: Optional[str] = None
    generated: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        if self.value is None:
            # Generate a cryptographically secure random value if not provided
            self.value = str(uuid.uuid4())
            self.generated = True

    @property
    def path(self) -> str:
        """Return the path in Vault where the secret is stored."""
        return f"/system/{self.namespace}/{self.name}"

    def __repr__(self) -> str:
        return f"Secret(path={self.path}, key={self.key}, value=***, environment={self.environment})"

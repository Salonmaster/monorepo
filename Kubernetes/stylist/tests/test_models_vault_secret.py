import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from stylist.models.vault_secret import VaultSecret


def test_vault_secret_with_value():
    """Test VaultSecret when value is provided."""
    secret = VaultSecret(
        namespace="test-ns",
        name="test-secret",
        key="password",
        value="my-password",
        environment="tst"
    )
    assert secret.value == "my-password"
    assert secret.generated is False
    assert secret.path == "/system/test-ns/test-secret"
    assert "password" in repr(secret)
    assert "***" in repr(secret)  # Value should be masked


def test_vault_secret_generates_value():
    """Test VaultSecret generates value when None is provided."""
    secret = VaultSecret(
        namespace="test-ns",
        name="test-secret",
        key="password",
        value=None,
        environment="tst"
    )
    assert secret.value is not None
    assert len(secret.value) > 0
    assert secret.generated is True
    assert secret.path == "/system/test-ns/test-secret"


def test_vault_secret_path():
    """Test VaultSecret path property."""
    secret = VaultSecret(
        namespace="my-namespace",
        name="my-secret",
        key="key1"
    )
    assert secret.path == "/system/my-namespace/my-secret"

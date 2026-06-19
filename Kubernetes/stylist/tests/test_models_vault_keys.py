import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from stylist.models.vault_keys import VaultKeys


def test_vault_keys_initialization():
    """Test VaultKeys initialization."""
    keys = VaultKeys(
        unseal_keys=["key1", "key2", "key3"],
        root_token="root-token-123"
    )
    assert keys.unseal_keys == ["key1", "key2", "key3"]
    assert keys.root_token == "root-token-123"


def test_vault_keys_print_keys():
    """Test VaultKeys print_keys method."""
    keys = VaultKeys(
        unseal_keys=["key1", "key2"],
        root_token="root-token"
    )
    
    with patch("stylist.models.vault_keys.typer.secho") as mock_secho:
        keys.print_keys()
        
        # Should print 2 unseal keys + 1 root token = 3 calls
        assert mock_secho.call_count == 3
        calls = [str(call) for call in mock_secho.call_args_list]
        assert any("Unseal Key 1" in str(call) for call in calls)
        assert any("Unseal Key 2" in str(call) for call in calls)
        assert any("Root Token" in str(call) for call in calls)


def test_vault_keys_empty_keys():
    """Test VaultKeys with empty unseal keys."""
    keys = VaultKeys(unseal_keys=[], root_token="token")
    
    with patch("stylist.models.vault_keys.typer.secho") as mock_secho:
        keys.print_keys()
        
        # Should only print root token
        assert mock_secho.call_count == 1
        assert any("Root Token" in str(call) for call in mock_secho.call_args_list)

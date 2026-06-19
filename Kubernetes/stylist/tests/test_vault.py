import sys
import types
import importlib.util
from pathlib import Path
import uuid

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STYLIST_ROOT = ROOT / "stylist"
if str(STYLIST_ROOT) not in sys.path:
    sys.path.insert(0, str(STYLIST_ROOT))

# Provide a stub for pysqlcipher3 if it's not installed
from stylist.tests.test_utils import ensure_pysqlcipher3_stub
ensure_pysqlcipher3_stub()

spec_db = importlib.util.spec_from_file_location("db", str(STYLIST_ROOT / "helpers" / "database.py"))
db = importlib.util.module_from_spec(spec_db)
spec_db.loader.exec_module(db)  # type: ignore

spec_vault = importlib.util.spec_from_file_location("vault", str(STYLIST_ROOT / "helpers" / "vault.py"))
vault = importlib.util.module_from_spec(spec_vault)
spec_vault.loader.exec_module(vault)  # type: ignore

spec_enums = importlib.util.spec_from_file_location("enums", str(STYLIST_ROOT / "enums" / "environment.py"))
enums = importlib.util.module_from_spec(spec_enums)
spec_enums.loader.exec_module(enums)  # type: ignore


def test_load_secrets(tmp_path):
    db_path = tmp_path / "secrets.db"
    pwd = db.create_database(str(db_path))
    db.upsert_secret(str(db_path), "ns", "foo", "password", "bar", None, pwd)
    secrets = db.load_secrets(str(db_path), pwd)
    assert len(secrets) == 1
    assert secrets[0].path == "/system/ns/foo"
    assert secrets[0].key == "password"
    assert secrets[0].value == "bar"


def test_store_secrets(monkeypatch, tmp_path):
    db_path = tmp_path / "s.db"
    pwd = db.create_database(str(db_path))
    db.upsert_secret(str(db_path), "ns", "app", "first", "val1", None, pwd)
    db.upsert_secret(str(db_path), "ns", "app", "second", None, "tst", pwd)

    vault_api_calls = []

    class MockVaultClient:
        def __init__(self, *args, **kwargs):
            self.secrets = types.SimpleNamespace(kv=types.SimpleNamespace(v2=self))

        def create_or_update_secret(self, mount_point, path, secret):
            vault_api_calls.append((mount_point, path, secret))

    monkeypatch.setattr(vault.hvac, "Client", MockVaultClient)

    secrets = db.load_secrets(str(db_path), pwd)
    vault.store_secrets(secrets, "token", url="http://localhost:8200")

    assert vault_api_calls[0][1] == "/system/ns/app"
    data = vault_api_calls[0][2]
    assert data["first"] == "val1"
    # Check that 'second' is a valid UUID string (generated when value is None)
    uuid.UUID(data["second"])  # raises ValueError if not a valid UUID


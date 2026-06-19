import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.tests.test_utils import ensure_sqlcipher3_stub  # noqa: E402

ensure_sqlcipher3_stub()

from stylist.helpers import database as db  # noqa: E402
import enums  # noqa: E402


def test_create_database_and_test_connection(tmp_path):
    db_path = tmp_path / "secrets.db"

    password = db.create_database(str(db_path), password="pw")

    assert db_path.exists()
    assert db.test_db_connection(str(db_path), password)


def test_upsert_and_load_secrets_filtered(tmp_path):
    db_path = tmp_path / "secrets.db"
    password = db.create_database(str(db_path), password="pw")

    db.upsert_secret(str(db_path), "ns", "app", "password", "secret", "tst", password)
    db.upsert_secret(str(db_path), "ns", "shared", "token", "shared-value", None, password)

    all_secrets = db.load_secrets(str(db_path), password)
    assert {s.name for s in all_secrets} == {"app", "shared"}

    filtered = db.load_secrets(str(db_path), password, enums.Environment.TST)
    assert {s.name for s in filtered} == {"app", "shared"}

    filtered_acc = db.load_secrets(str(db_path), password, enums.Environment.ACC)
    assert [s.name for s in filtered_acc] == ["shared"]


def test_change_database_password(tmp_path):
    db_path = tmp_path / "secrets.db"
    db.create_database(str(db_path), password="old")

    db.change_database_password(str(db_path), "old", "new")

    assert db.test_db_connection(str(db_path), "new")

import sys
import types
import importlib.util
from pathlib import Path

import pytest
import typer
import typer.testing

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

spec = importlib.util.spec_from_file_location("db", str(STYLIST_ROOT / "helpers" / "database.py"))
db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db)  # type: ignore

helpers_stub = types.ModuleType("helpers")
helpers_stub.database = db
sys.modules["helpers"] = helpers_stub

spec_cmd = importlib.util.spec_from_file_location("db_cmd", str(STYLIST_ROOT / "commands" / "database.py"))
db_cmd = importlib.util.module_from_spec(spec_cmd)
spec_cmd.loader.exec_module(db_cmd)  # type: ignore

runner = typer.testing.CliRunner()


def test_create_and_verify(tmp_path):
    db_path = tmp_path / "secrets.db"
    pwd = db.create_database(str(db_path))
    assert db_path.exists()
    assert db.test_db_connection(str(db_path), pwd)


def test_upsert_and_remove_secret(tmp_path):
    db_path = tmp_path / "secrets.db"
    pwd = db.create_database(str(db_path))

    db.upsert_secret(str(db_path), "ns", "foo", "password", "bar", "tst", pwd)
    conn = db.get_db_connection(str(db_path), pwd)
    cur = conn.cursor()
    cur.execute("SELECT Environment, Namespace, Name, Key, Value FROM secrets")
    row = cur.fetchone()
    assert row == ("tst", "ns", "foo", "password", "bar")
    conn.close()

    db.remove_secret(str(db_path), "ns", "foo", "password", "tst", pwd)
    conn = db.get_db_connection(str(db_path), pwd)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM secrets")
    assert cur.fetchone()[0] == 0
    conn.close()


def test_cli_verify(tmp_path):
    db_path = tmp_path / "secrets.db"
    pwd = db.create_database(str(db_path))
    result = runner.invoke(db_cmd._db_app, ["verify", str(db_path), "--password", pwd])
    assert result.exit_code == 0


def test_cli_create_set_remove(tmp_path):
    db_path = tmp_path / "cli.db"
    result = runner.invoke(db_cmd._db_app, ["create", str(db_path), "--password", "pw"])
    assert result.exit_code == 0
    assert db_path.exists()

    result = runner.invoke(
        db_cmd._db_app,
        [
            "set",
            str(db_path),
            "ns",
            "foo",
            "--key",
            "password",
            "--value",
            "bar",
            "--environment",
            "tst",
            "--password",
            "pw",
        ],
    )
    assert result.exit_code == 0
    conn = db.get_db_connection(str(db_path), "pw")
    cur = conn.cursor()
    cur.execute("SELECT Value FROM secrets WHERE Name='foo' AND Key='password'")
    assert cur.fetchone()[0] == "bar"
    conn.close()

    result = runner.invoke(
        db_cmd._db_app,
        [
            "remove",
            str(db_path),
            "ns",
            "foo",
            "--key",
            "password",
            "--environment",
            "tst",
            "--password",
            "pw",
        ],
    )
    assert result.exit_code == 0
    conn = db.get_db_connection(str(db_path), "pw")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM secrets")
    assert cur.fetchone()[0] == 0
    conn.close()


def test_cli_cluster_credentials(tmp_path):
    db_path = tmp_path / "cluster.db"
    runner.invoke(
        db_cmd._db_app,
        [
            "create",
            str(db_path),
            "--password",
            "pw",
        ],
    )

    result = runner.invoke(
        db_cmd._db_app,
        [
            "cluster-credentials",
            str(db_path),
            "--password",
            "pw",
            "--environment",
            "tst",
            "--cluster-password",
            "adminpw",
            "--repmgr-password",
            "reppw",
        ],
    )
    assert result.exit_code == 0

    conn = db.get_db_connection(str(db_path), "pw")
    cur = conn.cursor()
    cur.execute(
        "SELECT Key, Value, Environment FROM secrets WHERE Namespace=? AND Name=? ORDER BY Key",
        ("database-system", "cluster-credentials"),
    )
    rows = cur.fetchall()
    conn.close()

    assert rows == [
        ("password", "adminpw", "tst"),
        ("repmgr-password", "reppw", "tst"),
    ]


def test_change_password(tmp_path):
    db_path = tmp_path / "secrets.db"
    old_pwd = "oldpass"
    new_pwd = "newpass"

    db.create_database(str(db_path), old_pwd)
    db.change_database_password(str(db_path), old_pwd, new_pwd)
    assert db.test_db_connection(str(db_path), new_pwd)


def test_create_existing_db(tmp_path):
    db_path = tmp_path / "secrets.db"
    db.create_database(str(db_path))
    with pytest.raises(typer.Exit):
        db.create_database(str(db_path))

import sys
from pathlib import Path

# The project root is two levels above this file (stylist/tests/test_cli.py -> stylist -> project root)
ROOT = Path(__file__).resolve().parents[2]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

# Add stylist directory to path to allow importing core, models, etc.
STYLIST_DIR = ROOT / "stylist"
STYLIST_STR = str(STYLIST_DIR)
if STYLIST_STR not in sys.path:
    sys.path.insert(0, STYLIST_STR)

# Set up sqlcipher3 stub before any imports that might need it
sys.path.insert(0, str(STYLIST_DIR / "tests"))
from test_utils import ensure_sqlcipher3_stub
ensure_sqlcipher3_stub()

from typer.testing import CliRunner
import pytest

# Import core module from the stylist package path
import core

# Ensure Backbone is initialized
_ = core.Backbone()

@pytest.fixture(scope="session", autouse=True)
def register_commands():
    """Register CLI commands once per test session."""
    # Console is already mocked in conftest.py to prevent hanging
    # Import main to register commands - this happens once per session
    import stylist.main  # noqa: F401
    yield

runner = CliRunner()

def _invoke(args: list[str]):
    """Helper to run the Stylist CLI in tests."""
    return runner.invoke(core.Backbone().typer_app, args)


def test_cli_help_lists_core_commands():
    result = _invoke(["--help"])
    assert result.exit_code == 0
    for command in ("cluster", "database", "proxy"):
        assert command in result.stdout


def test_cli_database_create_and_verify(tmp_path):
    db_path = tmp_path / "cli.db"

    create_result = _invoke([
        "database",
        "create",
        str(db_path),
        "--password",
        "pw",
    ])
    assert create_result.exit_code == 0
    assert db_path.exists()

    verify_result = _invoke([
        "database",
        "verify",
        str(db_path),
        "--password",
        "pw",
    ])
    assert verify_result.exit_code == 0


def test_cli_database_change_password(tmp_path):
    db_path = tmp_path / "cli.db"
    _invoke([
        "database",
        "create",
        str(db_path),
        "--password",
        "pw",
    ])

    change_result = _invoke([
        "database",
        "changepassword",
        str(db_path),
        "--old-password",
        "pw",
        "--new-password",
        "newpw",
        "--confirm-password",
        "newpw",
    ])
    assert change_result.exit_code == 0

    verify_result = _invoke([
        "database",
        "verify",
        str(db_path),
        "--password",
        "newpw",
    ])
    assert verify_result.exit_code == 0


def test_cli_database_gui_help():
    result = _invoke([
        "database",
        "gui",
        "--help",
    ])
    assert result.exit_code == 0
    assert "database editor GUI" in result.stdout

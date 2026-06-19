import enums
import typer
import models
from sqlcipher3 import dbapi2 as sqlite
import secrets as secrets_mod
from pathlib import Path
from typing import Optional, List

def get_db_connection(db_path: str, password: str = None) -> sqlite.Connection:
    conn = sqlite.connect(db_path)
    if password:
        conn.execute(f"PRAGMA key = '{password}'")
    return conn

def test_db_connection(
    db_path: str,
    password: str = None,
    silent: bool = False,
    display_path: str | None = None,
) -> bool:
    target = display_path or db_path
    if not silent:
        typer.echo(f"🔍 Testing database connection to {target}... ", nl=False)
    try:
        conn = get_db_connection(db_path, password)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'")
        result = cursor.fetchone()
        conn.close()
        if not silent:
            if result is not None:
                typer.secho("OK", fg=typer.colors.GREEN)
            else:
                typer.secho("Failed", fg=typer.colors.RED)
        return result is not None
    except Exception as e:
        if not silent:
            typer.secho("Failed", fg=typer.colors.RED)
            typer.secho(f"Reason: {e}", fg=typer.colors.RED)
            typer.secho("Please check your database path and password.", fg=typer.colors.RED)
            typer.secho("If the database is encrypted, ensure you provide the correct password.", fg=typer.colors.RED)
            typer.secho("If the database is not encrypted, try without a password.", fg=typer.colors.RED)
            typer.secho("If the database does not exist, please create it first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def create_database(
    db_path: str,
    password: Optional[str] = None,
    silent: bool = False,
    display_path: str | None = None,
) -> str:
    """Create a new encrypted secrets database.

    Args:
        db_path: Path where the database will be created.
        password: Optional password to encrypt the database. If ``None`` a
            random password will be generated.

    Returns:
        The password that was used to create the database.
    """
    path = Path(db_path)

    if path.exists():
        typer.secho("Database already exists.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if password is None:
        password = secrets_mod.token_urlsafe(16)

    target = display_path or db_path
    if not silent:
        typer.echo(f"🗄️  Creating secrets database at {target}... ", nl=False)
    conn = sqlite.connect(db_path)
    conn.execute(f"PRAGMA key = '{password}'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS secrets ("
        "ID INTEGER PRIMARY KEY AUTOINCREMENT,"
        "Environment TEXT,"
        "Namespace TEXT NOT NULL,"
        "Name TEXT NOT NULL,"
        "Key TEXT NOT NULL,"
        "Value TEXT"
        ")"
    )
    conn.commit()
    conn.close()
    if not silent:
        typer.secho("OK", fg=typer.colors.GREEN)
    return password


def upsert_secret(
    db_path: str,
    namespace: str,
    name: str,
    key: str,
    value: Optional[str],
    environment: Optional[str],
    password: Optional[str] = None,
    silent: bool = False,
) -> None:
    """Insert or update a secret record in the database."""
    conn = get_db_connection(db_path, password)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ID FROM secrets WHERE Name=? AND Namespace=? AND Key=? AND "
        "(Environment=? OR (? IS NULL AND Environment IS NULL))",
        (name, namespace, key, environment, environment),
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE secrets SET Value=?, Environment=? WHERE ID=?",
            (value, environment, row[0]),
        )
    else:
        cursor.execute(
            "INSERT INTO secrets (Environment, Namespace, Name, Key, Value) "
            "VALUES (?, ?, ?, ?, ?)",
            (environment, namespace, name, key, value),
        )
    conn.commit()
    conn.close()
    if not silent:
        typer.secho("Secret stored", fg=typer.colors.GREEN)

def remove_secret(
    db_path: str,
    namespace: str,
    name: str,
    key: str,
    environment: Optional[str],
    password: Optional[str] = None,
    silent: bool = False,
) -> bool:
    """Remove a secret record from the database.

    Returns:
        True if the secret was removed, False if it was not found.
    """
    conn = get_db_connection(db_path, password)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM secrets WHERE Name=? AND Namespace=? AND Key=? AND (Environment=? OR (? IS NULL AND Environment IS NULL))",
        (name, namespace, key, environment, environment),
    )
    conn.commit()
    removed = cursor.rowcount > 0
    conn.close()
    if not silent:
        if removed:
            typer.secho("Secret removed", fg=typer.colors.GREEN)
        else:
            typer.secho("Secret not found", fg=typer.colors.YELLOW)
    return removed


def fetch_all_secrets(
    db_path: str,
    password: Optional[str] = None,
    env: enums.Environment | None = None,
) -> list[tuple[str | None, str, str, str, str | None]]:
    """Retrieve all secrets from the database, optionally filtering by environment."""
    conn = get_db_connection(db_path, password)
    cursor = conn.cursor()
    cursor.execute("SELECT Environment, Namespace, Name, Key, Value FROM secrets")
    rows = cursor.fetchall()
    conn.close()

    if env is None:
        return rows

    env_value = env.value if isinstance(env, enums.Environment) else str(env)
    return [
        (row_env, ns, name, key, value)
        for row_env, ns, name, key, value in rows
        if row_env is None or row_env == env_value
    ]


def load_secrets(
    db_path: str,
    password: Optional[str] = None,
    env: enums.Environment | None = None,
) -> List[models.VaultSecret]:
    """Load secrets from the database as ``VaultSecret`` objects."""
    rows = fetch_all_secrets(db_path, password, env)
    return [
        models.VaultSecret(
            namespace=namespace,
            name=name,
            key=key,
            value=value,
            environment=row_env,
        )
        for row_env, namespace, name, key, value in rows
    ]


def change_database_password(
    db_path: str,
    old_password: Optional[str],
    new_password: Optional[str],
) -> None:
    """Change the encryption password for the secrets database."""

    if not new_password:
        raise typer.BadParameter("New password cannot be empty")

    conn = get_db_connection(db_path, old_password)
    try:
        cursor = conn.cursor()
        escaped_pwd = new_password.replace("'", "''")
        cursor.execute(f"PRAGMA rekey = '{escaped_pwd}'")
        conn.commit()
    finally:
        conn.close()


class Credential:
    """Simple credential object with name and password attributes."""
    def __init__(self, name: str, password: str, username: str = ""):
        self.name = name
        self.password = password
        self.username = username


def add_credential(
    db_path: str,
    db_password: Optional[str],
    name: str,
    username: str,
    password: str,
) -> None:
    """Add or update a credential in the database.

    Credentials are stored as secrets with namespace 'stylist-credentials'.

    Args:
        db_path: Path to the database file
        db_password: Password for the database encryption
        name: Name of the credential
        username: Username for the credential
        password: Password for the credential
    """
    upsert_secret(
        db_path=db_path,
        namespace="stylist-credentials",
        name=name,
        key="password",
        value=password,
        environment=None,
        password=db_password,
        silent=True,
    )
    if username:
        upsert_secret(
            db_path=db_path,
            namespace="stylist-credentials",
            name=name,
            key="username",
            value=username,
            environment=None,
            password=db_password,
            silent=True,
        )


def get_credentials(
    db_path: str,
    password: Optional[str] = None,
) -> List[Credential]:
    """Retrieve all credentials from the database.

    Returns a list of Credential objects with name, password, and username attributes.
    """
    conn = get_db_connection(db_path, password)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT Name, Key, Value FROM secrets WHERE Namespace='stylist-credentials'"
    )
    rows = cursor.fetchall()
    conn.close()

    # Group by credential name
    credentials_dict: dict[str, dict[str, str]] = {}
    for name, key, value in rows:
        if name not in credentials_dict:
            credentials_dict[name] = {}
        credentials_dict[name][key] = value

    # Convert to Credential objects
    credentials = []
    for name, fields in credentials_dict.items():
        cred_password = fields.get("password", "")
        cred_username = fields.get("username", "")
        credentials.append(Credential(name=name, password=cred_password, username=cred_username))

    return credentials

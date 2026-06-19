import os
import typer
import enums
from stylist import helpers
from stylist.helpers import remote_db
import core


def _resolve_secrets_db(
    db: str | None,
    *,
    download: bool = True,
    auto_cleanup: bool = True,
) -> tuple[str, remote_db.SecretsDatabaseHandle | None]:
    if not db:
        raise typer.BadParameter("Database path required")
    db_path = db
    if remote_db.is_s3_path(db_path):
        db_path = remote_db.normalize_s3_path(db_path)
    local_path, handle = remote_db.prepare_secrets_db(
        db_path,
        download=download,
        auto_cleanup=auto_cleanup,
    )
    return (local_path or db_path), handle


def _ensure_secret_value(value: str | None, prompt_text: str) -> str:
    """Prompt the user for a secret value if it was not provided."""
    if value is not None:
        return value
    return typer.prompt(prompt_text, hide_input=True, confirmation_prompt=True)
from console import database_editor

# Create a typer app for database subcommands
_db_app = typer.Typer(help="Manage the secrets database")


@_db_app.callback(invoke_without_command=True)
def _database_group(ctx: typer.Context):
    """Database command group entrypoint."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


@_db_app.command("verify")
def verify(
    db: str | None = typer.Argument(
        None,
        help="Path to the secrets database",
        envvar="SECRETS_DB"
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
):
    """Verify that a secrets database exists and can be opened."""

    db_path, handle = _resolve_secrets_db(db)
    try:
        helpers.database.test_db_connection(
            db_path,
            password,
            display_path=handle.source_path if handle else db_path,
        )
    finally:
        if handle:
            handle.close()


@_db_app.command("create")
def create(
    path: str | None = typer.Argument(
        None,
        help="Path of the database to create",
        envvar="SECRETS_DB"
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Password for the database",
        envvar="SECRETS_DB_PASSWORD",
    ),
):
    """Create a new encrypted secrets database."""
    db_path, handle = _resolve_secrets_db(path, download=False)
    try:
        pwd = helpers.database.create_database(
            db_path,
            password,
            display_path=handle.source_path if handle else db_path,
        )
        if handle:
            handle.mark_dirty()
    finally:
        if handle:
            handle.close()
    if password is None:
        typer.secho(f"Generated database password: {pwd}", fg=typer.colors.BRIGHT_GREEN)


@_db_app.command("set")
def set_secret(
    db: str | None = typer.Argument(
        None, help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
    namespace: str | None = typer.Argument(
        None, help="Kubernetes namespace"
    ),
    name: str | None = typer.Argument(
        None, help="Secret name"
    ),
    key: str = typer.Option(
        "value",
        "--key",
        "-k",
        help="Secret data key",
        envvar="SECRET_KEY",
    ),
    value: str = typer.Option(
        None,
        "--value",
        "-v",
        help="Secret value",
        envvar="SECRET_VALUE",
    ),
    environment: enums.Environment = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment",
        envvar="ENV",
    ),
):
    """Insert or update a secret in the database."""
    name = name or os.getenv("STYLIST_SECRET_NAME")
    if not all([db, namespace, name]):
        raise typer.BadParameter("db, namespace and name are required")
    db_path, handle = _resolve_secrets_db(db)
    try:
        helpers.database.upsert_secret(
            db_path=db_path,
            namespace=namespace,
            name=name,
            key=key,
            value=value,
            environment=environment.value if environment else None,
            password=password,
        )
        if handle:
            handle.mark_dirty()
    finally:
        if handle:
            handle.close()


@_db_app.command("cluster-credentials")
def add_cluster_credentials(
    db: str | None = typer.Argument(
        None,
        help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
    environment: enums.Environment = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment",
        envvar="ENV",
    ),
    cluster_password: str | None = typer.Option(
        None,
        "--cluster-password",
        help="PostgreSQL superuser password",
    ),
    repmgr_password: str | None = typer.Option(
        None,
        "--repmgr-password",
        help="Password for the repmgr user",
    ),
    namespace: str = typer.Option(
        "database-system",
        "--namespace",
        help="Namespace used to build the Vault secret path",
        show_default=True,
    ),
    name: str = typer.Option(
        "cluster-credentials",
        "--name",
        help="Secret name stored in Vault",
        show_default=True,
    ),
):
    """Store the cluster-credentials secret in the database."""

    cluster_password = _ensure_secret_value(cluster_password, "Cluster superuser password")
    repmgr_password = _ensure_secret_value(repmgr_password, "repmgr password")

    db_path, handle = _resolve_secrets_db(db)
    env_value = environment.value if environment else None

    try:
        helpers.database.upsert_secret(
            db_path=db_path,
            namespace=namespace,
            name=name,
            key="password",
            value=cluster_password,
            environment=env_value,
            password=password,
        )
        helpers.database.upsert_secret(
            db_path=db_path,
            namespace=namespace,
            name=name,
            key="repmgr-password",
            value=repmgr_password,
            environment=env_value,
            password=password,
        )
        if handle:
            handle.mark_dirty()
    finally:
        if handle:
            handle.close()

    typer.secho(
        f"Stored cluster credentials for {namespace}/{name}"
        + (f" (environment: {env_value})" if env_value else " (shared)"),
        fg=typer.colors.GREEN,
    )


@_db_app.command("remove")
def remove_secret(
    db: str | None = typer.Argument(
        None, help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    namespace: str | None = typer.Argument(
        None, help="Kubernetes namespace"
    ),
    name: str | None = typer.Argument(
        None, help="Secret name"
    ),
    key: str = typer.Option(
        "value",
        "--key",
        "-k",
        help="Secret data key",
        envvar="SECRET_KEY",
    ),
    environment: enums.Environment = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment",
        envvar="ENV",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
):
    """Remove a secret from the database."""
    if not all([db, namespace, name]):
        raise typer.BadParameter("db, namespace and name are required")
    db_path, handle = _resolve_secrets_db(db)
    try:
        helpers.database.remove_secret(
            db_path=db_path,
            namespace=namespace,
            name=name,
            key=key,
            environment=environment.value if environment else None,
            password=password,
        )
        if handle:
            handle.mark_dirty()
    finally:
        if handle:
            handle.close()


@_db_app.command("gui")
def edit_gui(
    db: str | None = typer.Argument(
        None,
        help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
    environment: enums.Environment | None = typer.Option(
        None,
        "--environment",
        "-e",
        help="Pre-select an environment filter",
        envvar="ENV",
    ),
    shared_only: bool = typer.Option(
        False,
        "--shared-only",
        help="Show only secrets without an environment",
    ),
):
    """Open the Stylist database editor GUI."""
    if not db:
        raise typer.BadParameter("Database path required")
    if shared_only and environment is not None:
        raise typer.BadParameter("Choose either --environment or --shared-only")

    db_path, handle = _resolve_secrets_db(db, auto_cleanup=False)
    try:
        helpers.database.test_db_connection(
            db_path,
            password,
            display_path=handle.source_path if handle else db_path,
        )
    except Exception:
        if handle:
            handle.cleanup()
        raise

    core.Backbone().context.secrets_db = db_path
    core.Backbone().context.secrets_db_password = password

    filter_value: str | None = None
    if shared_only:
        filter_value = database_editor.FILTER_SHARED
    elif environment is not None:
        filter_value = environment.value

    app = database_editor.DatabaseEditorApp(
        db_path=db_path,
        password=password,
        environment_filter=filter_value,
        db_handle=handle,
    )
    try:
        app.run()
    finally:
        if handle:
            handle.sync()
            handle.cleanup()


@_db_app.command("changepassword")
def change_password(
    db: str | None = typer.Argument(
        None,
        help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    old_password: str = typer.Option(
        None,
        "--old-password",
        help="Current database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
    new_password: str = typer.Option(
        None,
        "--new-password",
        help="New database password",
    ),
    confirm_password: str = typer.Option(
        None,
        "--confirm-password",
        help="Confirm the new password",
    ),
):
    """Change the encryption password for the secrets database."""

    db_path, handle = _resolve_secrets_db(db, auto_cleanup=False)

    if not new_password:
        raise typer.BadParameter("New password required")
    if confirm_password is not None and confirm_password != new_password:
        raise typer.BadParameter("New password confirmation does not match")

    try:
        helpers.database.test_db_connection(
            db_path,
            old_password,
            display_path=handle.source_path if handle else db_path,
        )
        helpers.database.change_database_password(
            db_path=db_path,
            old_password=old_password,
            new_password=new_password,
        )
        if handle:
            handle.mark_dirty()
        typer.secho("Database password updated", fg=typer.colors.GREEN)
    finally:
        if handle:
            handle.close()


@_db_app.command("sync")
def sync_secrets(
    db: str | None = typer.Argument(
        None,
        help="Path to the secrets database",
        envvar="SECRETS_DB",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Database password",
        envvar="SECRETS_DB_PASSWORD",
    ),
    environment: enums.Environment = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment to sync",
        envvar="ENV",
    ),
    direction: str = typer.Option(
        "both",
        "--direction",
        "-d",
        help="Sync direction: 'db-to-vault', 'vault-to-db', or 'both'",
    ),
    vault_token: str = typer.Option(
        None,
        "--vault-token",
        help="Vault root token (required if not in context)",
    ),
    vault_url: str = typer.Option(
        None,
        "--vault-url",
        help="Vault URL (defaults to port-forward)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be synced without making changes",
    ),
    namespace: str | None = typer.Option(
        None,
        "--namespace",
        help="Filter by namespace",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Filter by secret name",
    ),
):
    """Sync secrets between the database and HashiCorp Vault."""
    from stylist.helpers import vault

    if not db:
        raise typer.BadParameter("Database path required")

    db_path, handle = _resolve_secrets_db(db)

    try:
        # Get vault token
        token = vault_token
        if not token:
            if core.Backbone().context.vault_keys:
                token = core.Backbone().context.vault_keys.root_token
            else:
                raise typer.BadParameter("Vault token required (use --vault-token or set in context)")

        # Get vault URL
        vault_url_final = vault_url

        # Load secrets from database
        env_enum = environment if environment else None
        db_secrets = helpers.database.load_secrets(
            db_path=db_path,
            password=password,
            env=env_enum,
        )

        typer.echo(f"📊 Found {len(db_secrets)} secrets in database")

        # Load secrets from Vault
        with vault.port_forward_vault() as port_forward_url:
            vault_url_to_use = vault_url_final or port_forward_url
            vault_secrets = vault.read_secrets(
                root_token=token,
                url=vault_url_to_use,
                namespace=namespace,
                name=name,
            )

        typer.echo(f"📊 Found {len(vault_secrets)} secrets in Vault")

        # Create lookup dictionaries for comparison
        db_lookup = {
            (s.namespace, s.name, s.key): s
            for s in db_secrets
        }
        vault_lookup = {
            (s.namespace, s.name, s.key): s
            for s in vault_secrets
        }

        # Find differences
        db_only = []
        vault_only = []
        different = []

        all_keys = set(db_lookup.keys()) | set(vault_lookup.keys())

        for key in all_keys:
            db_secret = db_lookup.get(key)
            vault_secret = vault_lookup.get(key)

            if db_secret and not vault_secret:
                db_only.append(db_secret)
            elif vault_secret and not db_secret:
                vault_only.append(vault_secret)
            elif db_secret and vault_secret:
                if db_secret.value != vault_secret.value:
                    different.append((db_secret, vault_secret))

        # Report differences
        if db_only:
            typer.echo(f"\n🔵 Secrets only in database ({len(db_only)}):")
            for secret in db_only:
                typer.echo(f"  - {secret.namespace}/{secret.name}.{secret.key}")

        if vault_only:
            typer.echo(f"\n🟢 Secrets only in Vault ({len(vault_only)}):")
            for secret in vault_only:
                typer.echo(f"  - {secret.namespace}/{secret.name}.{secret.key}")

        if different:
            typer.echo(f"\n🟡 Secrets with different values ({len(different)}):")
            for db_sec, vault_sec in different:
                typer.echo(f"  - {db_sec.namespace}/{db_sec.name}.{db_sec.key}")
                typer.echo(f"    DB:    {db_sec.value[:20]}..." if len(db_sec.value or '') > 20 else f"    DB:    {db_sec.value}")
                typer.echo(f"    Vault: {vault_sec.value[:20]}..." if len(vault_sec.value or '') > 20 else f"    Vault: {vault_sec.value}")

        if not db_only and not vault_only and not different:
            typer.secho("\n✅ Database and Vault are in sync!", fg=typer.colors.GREEN)
            return

        # Perform sync if not dry run
        if dry_run:
            typer.secho("\n🔍 Dry run - no changes made", fg=typer.colors.YELLOW)
            return

        synced_count = 0

        # Sync database to Vault
        if direction in ("db-to-vault", "both"):
            if db_only or different:
                secrets_to_sync = []
                for secret in db_only:
                    secrets_to_sync.append(secret)
                for db_sec, _ in different:
                    secrets_to_sync.append(db_sec)

                if secrets_to_sync:
                    typer.echo(f"\n📤 Syncing {len(secrets_to_sync)} secrets from database to Vault...")
                    with vault.port_forward_vault() as port_forward_url:
                        vault_url_to_use = vault_url_final or port_forward_url
                        if vault.store_secrets(secrets_to_sync, token, vault_url_to_use):
                            synced_count += len(secrets_to_sync)
                            typer.secho(f"✅ Synced {len(secrets_to_sync)} secrets to Vault", fg=typer.colors.GREEN)
                        else:
                            typer.secho("❌ Failed to sync secrets to Vault", fg=typer.colors.RED)

        # Sync Vault to database
        if direction in ("vault-to-db", "both"):
            if vault_only or different:
                secrets_to_sync = []
                for secret in vault_only:
                    secrets_to_sync.append(secret)
                for _, vault_sec in different:
                    secrets_to_sync.append(vault_sec)

                if secrets_to_sync:
                    typer.echo(f"\n📥 Syncing {len(secrets_to_sync)} secrets from Vault to database...")
                    for secret in secrets_to_sync:
                        helpers.database.upsert_secret(
                            db_path=db_path,
                            namespace=secret.namespace,
                            name=secret.name,
                            key=secret.key,
                            value=secret.value,
                            environment=env_enum.value if env_enum else None,
                            password=password,
                            silent=True,
                        )
                    synced_count += len(secrets_to_sync)
                    typer.secho(f"✅ Synced {len(secrets_to_sync)} secrets to database", fg=typer.colors.GREEN)
                    if handle:
                        handle.mark_dirty()

        if synced_count > 0:
            typer.secho(f"\n✅ Sync complete! Synced {synced_count} secrets.", fg=typer.colors.GREEN)
    finally:
        if handle:
            handle.close()


# Register the database command group with the main application
core.Backbone().typer_app.add_typer(_db_app, name="database")

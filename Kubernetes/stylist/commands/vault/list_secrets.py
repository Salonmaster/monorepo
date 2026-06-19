import typer
from stylist.helpers import vault as vault_helper
from stylist.models import vault_keys
import core
try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def list_secrets(
    namespace: str | None = typer.Option(
        None,
        "--namespace", "-n",
        help="Filter by namespace (e.g., database-system)",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Filter by secret name (e.g., cluster-credentials)",
    ),
    secrets_db: str | None = typer.Option(
        None,
        "--secrets-db", "-s",
        help="Path to the secrets database file to get root token",
        envvar="SECRETS_DB"
    ),
    secrets_db_password: str | None = typer.Option(
        None,
        "--secrets-db-password", "-p",
        help="Password for the secrets database",
        envvar="SECRETS_DB_PASSWORD"
    ),
    root_token: str | None = typer.Option(
        None,
        "--root-token", "-t",
        help="Vault root token (if not using secrets database)",
    ),
):
    """List secrets stored in Vault."""
    typer.secho("📋 Listing secrets from Vault...", fg=typer.colors.BRIGHT_BLUE)

    # Get root token
    token = root_token
    if not token and secrets_db:
        from stylist.helpers import database
        from stylist.helpers import remote_db

        local_db, _ = remote_db.prepare_secrets_db(
            secrets_db,
            auto_cleanup=True,
        )
        credentials = database.get_credentials(local_db, secrets_db_password)
        vault_cred = next((c for c in credentials if "vault" in c.name.lower() and "root" in c.name.lower()), None)
        if vault_cred:
            token = vault_cred.password
        else:
            typer.secho("❌ Could not find Vault root token in secrets database", fg=typer.colors.RED)
            typer.secho("   Please provide --root-token or ensure vault root token is in secrets database", fg=typer.colors.YELLOW)
            raise typer.Exit(1)

    if not token:
        token = typer.prompt("Vault root token", hide_input=True)

    namespace_filter = namespace or core.Backbone().context.vault_namespace if namespace else None

    try:
        with vault_helper.port_forward_vault(
            namespace=core.Backbone().context.vault_namespace,
            pod_name=core.Backbone().context.vault_pod_name,
        ) as vault_url:
            secrets = vault_helper.read_secrets(
                root_token=token,
                url=vault_url,
                namespace=namespace_filter,
                name=name,
            )

            if not secrets:
                typer.secho("📭 No secrets found", fg=typer.colors.YELLOW)
                if namespace_filter:
                    typer.secho(f"   (filtered by namespace: {namespace_filter})", fg=typer.colors.BRIGHT_BLACK)
                if name:
                    typer.secho(f"   (filtered by name: {name})", fg=typer.colors.BRIGHT_BLACK)
                return

            # Group secrets by path
            grouped: dict[str, list[str]] = {}
            for secret in secrets:
                path = f"{secret.namespace}/{secret.name}"
                if path not in grouped:
                    grouped[path] = []
                grouped[path].append(secret.key)

            if RICH_AVAILABLE:
                console = Console()
                table = Table(title="Vault Secrets")
                table.add_column("Path", style="cyan")
                table.add_column("Keys", style="green")

                for path, keys in sorted(grouped.items()):
                    table.add_row(path, ", ".join(sorted(keys)))

                console.print(table)
            else:
                typer.secho("\nVault Secrets:", fg=typer.colors.BRIGHT_BLUE, bold=True)
                for path, keys in sorted(grouped.items()):
                    typer.secho(f"  {path}: {', '.join(sorted(keys))}", fg=typer.colors.CYAN)
            typer.secho(f"\n✅ Found {len(secrets)} secret(s) across {len(grouped)} path(s)", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"❌ Error listing secrets: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

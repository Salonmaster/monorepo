import typer
from stylist.helpers import vault as vault_helper
import core
try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def read_secret(
    namespace: str = typer.Argument(..., help="Namespace of the secret (e.g., database-system)"),
    name: str = typer.Argument(..., help="Name of the secret (e.g., cluster-credentials)"),
    key: str | None = typer.Option(
        None,
        "--key", "-k",
        help="Specific key to read (if not provided, all keys are shown)",
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
    show_value: bool = typer.Option(
        False,
        "--show-value",
        help="Show the actual secret values (use with caution!)",
    ),
):
    """Read a secret from Vault."""
    typer.secho(f"📖 Reading secret: {namespace}/{name}", fg=typer.colors.BRIGHT_BLUE)
    
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
    
    try:
        with vault_helper.port_forward_vault(
            namespace=core.Backbone().context.vault_namespace,
            pod_name=core.Backbone().context.vault_pod_name,
        ) as vault_url:
            secrets = vault_helper.read_secrets(
                root_token=token,
                url=vault_url,
                namespace=namespace,
                name=name,
            )
            
            if not secrets:
                typer.secho(f"❌ Secret not found: {namespace}/{name}", fg=typer.colors.RED)
                raise typer.Exit(1)
            
            # Filter by key if specified
            if key:
                secrets = [s for s in secrets if s.key == key]
                if not secrets:
                    typer.secho(f"❌ Key '{key}' not found in secret {namespace}/{name}", fg=typer.colors.RED)
                    raise typer.Exit(1)
            
            if RICH_AVAILABLE:
                console = Console()
                table = Table(title=f"Secret: {namespace}/{name}")
                table.add_column("Key", style="cyan")
                if show_value:
                    table.add_column("Value", style="green")
                else:
                    table.add_column("Value", style="dim")
                
                for secret in sorted(secrets, key=lambda s: s.key):
                    if show_value:
                        table.add_row(secret.key, secret.value)
                    else:
                        table.add_row(secret.key, "***")
                
                console.print(table)
            else:
                typer.secho(f"\nSecret: {namespace}/{name}", fg=typer.colors.BRIGHT_BLUE, bold=True)
                for secret in sorted(secrets, key=lambda s: s.key):
                    value_display = secret.value if show_value else "***"
                    typer.secho(f"  {secret.key}: {value_display}", fg=typer.colors.CYAN)
            
            if not show_value:
                typer.secho("\n💡 Use --show-value to display actual values (use with caution!)", fg=typer.colors.YELLOW)
            
            typer.secho(f"\n✅ Found {len(secrets)} key(s)", fg=typer.colors.GREEN)
            
    except Exception as e:
        typer.secho(f"❌ Error reading secret: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

import typer
from stylist.helpers import vault as vault_helper
from stylist.models import vault_secret
import core


def write_secret(
    namespace: str = typer.Argument(..., help="Namespace of the secret (e.g., database-system)"),
    name: str = typer.Argument(..., help="Name of the secret (e.g., cluster-credentials)"),
    key: str = typer.Argument(..., help="Key name (e.g., password)"),
    value: str | None = typer.Option(
        None,
        "--value", "-v",
        help="Value to store (if not provided, will be prompted)",
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
    """Write a secret to Vault."""
    typer.secho(f"✍️  Writing secret: {namespace}/{name}/{key}", fg=typer.colors.BRIGHT_BLUE)
    
    # Get value if not provided
    secret_value = value
    if not secret_value:
        secret_value = typer.prompt(f"Value for {key}", hide_input=True)
    
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
        secret = vault_secret.VaultSecret(
            namespace=namespace,
            name=name,
            key=key,
            value=secret_value,
        )
        
        with vault_helper.port_forward_vault(
            namespace=core.Backbone().context.vault_namespace,
            pod_name=core.Backbone().context.vault_pod_name,
        ) as vault_url:
            success = vault_helper.store_secrets(
                secrets=[secret],
                root_token=token,
                url=vault_url,
            )
            
            if success:
                typer.secho(f"✅ Successfully wrote secret: {namespace}/{name}/{key}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"❌ Failed to write secret: {namespace}/{name}/{key}", fg=typer.colors.RED)
                raise typer.Exit(1)
            
    except Exception as e:
        typer.secho(f"❌ Error writing secret: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

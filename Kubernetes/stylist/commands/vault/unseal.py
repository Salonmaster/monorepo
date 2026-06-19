import typer
import asyncio
from stylist.helpers import vault as vault_helper
from stylist.models import vault_keys
import core
from stylist.helpers import database
from stylist.helpers import remote_db


def unseal(
    secrets_db: str = typer.Option(
        ...,
        "--secrets-db", "-s",
        help="Path to the secrets database file containing unseal keys",
        envvar="SECRETS_DB"
    ),
    secrets_db_password: str | None = typer.Option(
        None,
        "--secrets-db-password", "-p",
        help="Password for the secrets database",
        envvar="SECRETS_DB_PASSWORD"
    ),
):
    """Unseal Vault using keys from the secrets database."""
    typer.secho("🔓 Unsealing Vault...", fg=typer.colors.BRIGHT_BLUE)
    
    namespace = core.Backbone().context.vault_namespace
    pod_name = core.Backbone().context.vault_pod_name
    
    try:
        # Get vault keys from database
        local_db, _ = remote_db.prepare_secrets_db(
            secrets_db,
            auto_cleanup=True,
        )
        credentials = database.get_credentials(local_db, secrets_db_password)
        
        # Find vault keys credential
        vault_keys_cred = next((c for c in credentials if "vault" in c.name.lower() and "keys" in c.name.lower()), None)
        if not vault_keys_cred:
            typer.secho("❌ Could not find Vault keys in secrets database", fg=typer.colors.RED)
            typer.secho("   Please ensure vault keys are stored in the database", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
        
        # Parse unseal keys from credential (assuming they're stored in a specific format)
        # This is a simplified version - you may need to adjust based on how keys are stored
        unseal_keys = vault_keys_cred.password.split("\n") if "\n" in vault_keys_cred.password else [vault_keys_cred.password]
        unseal_keys = [k.strip() for k in unseal_keys if k.strip()]
        
        if len(unseal_keys) < 3:
            typer.secho("❌ Insufficient unseal keys found", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        vault_keys_obj = vault_keys.VaultKeys(unseal_keys[:5], "")  # Use first 5 keys
        
        typer.secho(f"   Using {len(unseal_keys)} unseal key(s)", fg=typer.colors.CYAN)
        typer.secho(f"   Namespace: {namespace}", fg=typer.colors.CYAN)
        typer.secho(f"   Pod: {pod_name}", fg=typer.colors.CYAN)
        
        success = asyncio.run(vault_helper.unseal_vault(
            vault_keys_obj,
            namespace=namespace,
            pod_name=pod_name,
        ))
        
        if success:
            typer.secho("✅ Vault unsealed successfully", fg=typer.colors.GREEN)
        else:
            typer.secho("❌ Failed to unseal Vault", fg=typer.colors.RED)
            raise typer.Exit(1)
            
    except Exception as e:
        typer.secho(f"❌ Error unsealing Vault: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

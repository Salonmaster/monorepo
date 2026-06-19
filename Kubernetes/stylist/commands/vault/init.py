import typer
import asyncio
from stylist.helpers import vault as vault_helper
from stylist.models import vault_keys
import core


def init(
    save_to_db: bool = typer.Option(
        False,
        "--save-to-db",
        help="Save the generated keys to the secrets database",
    ),
    secrets_db: str | None = typer.Option(
        None,
        "--secrets-db", "-s",
        help="Path to the secrets database file",
        envvar="SECRETS_DB"
    ),
    secrets_db_password: str | None = typer.Option(
        None,
        "--secrets-db-password", "-p",
        help="Password for the secrets database",
        envvar="SECRETS_DB_PASSWORD"
    ),
):
    """Initialize Vault and generate unseal keys and root token."""
    typer.secho("🔧 Initializing Vault...", fg=typer.colors.BRIGHT_BLUE)
    
    namespace = core.Backbone().context.vault_namespace
    pod_name = core.Backbone().context.vault_pod_name
    
    typer.secho(f"   Namespace: {namespace}", fg=typer.colors.CYAN)
    typer.secho(f"   Pod: {pod_name}", fg=typer.colors.CYAN)
    
    try:
        vault_keys_obj = asyncio.run(vault_helper.init_vault(
            namespace=namespace,
            pod_name=pod_name,
        ))
        
        if not vault_keys_obj:
            typer.secho("❌ Failed to initialize Vault", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        typer.secho("\n✅ Vault initialized successfully!", fg=typer.colors.GREEN)
        typer.secho("\n🔑 Generated Keys:", fg=typer.colors.BRIGHT_YELLOW, bold=True)
        vault_keys_obj.print_keys()
        
        typer.secho("\n⚠️  IMPORTANT: Store these keys securely!", fg=typer.colors.RED, bold=True)
        typer.secho("   You will need at least 3 unseal keys to unseal Vault.", fg=typer.colors.YELLOW)
        
        if save_to_db and secrets_db:
            from stylist.helpers import database
            from stylist.helpers import remote_db
            
            typer.secho("\n💾 Saving keys to secrets database...", fg=typer.colors.BRIGHT_BLUE)
            # Ensure secrets_db is a string, not an OptionInfo object
            secrets_db_str = str(secrets_db) if secrets_db else None
            local_db, _ = remote_db.prepare_secrets_db(
                secrets_db_str,
                auto_cleanup=True,
            )
            
            # Save unseal keys
            keys_value = "\n".join(vault_keys_obj.unseal_keys)
            database.add_credential(
                db_path=local_db,
                db_password=secrets_db_password,
                name="Vault Unseal Keys",
                username="vault",
                password=keys_value,
            )
            
            # Save root token
            database.add_credential(
                db_path=local_db,
                db_password=secrets_db_password,
                name="Vault Root Token",
                username="vault",
                password=vault_keys_obj.root_token,
            )
            
            typer.secho("✅ Keys saved to secrets database", fg=typer.colors.GREEN)
        elif save_to_db:
            typer.secho("⚠️  --save-to-db requires --secrets-db to be specified", fg=typer.colors.YELLOW)
            
    except Exception as e:
        typer.secho(f"❌ Error initializing Vault: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

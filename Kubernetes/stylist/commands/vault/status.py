import typer
import asyncio
from stylist.helpers import vault as vault_helper
import core


def status():
    """Check the status of Vault."""
    typer.secho("🔍 Checking Vault status...", fg=typer.colors.BRIGHT_BLUE)
    
    namespace = core.Backbone().context.vault_namespace
    pod_name = core.Backbone().context.vault_pod_name
    
    try:
        is_connected = asyncio.run(vault_helper.check_vault_connection())
        if is_connected:
            typer.secho("✅ Vault is accessible and responding", fg=typer.colors.GREEN)
            typer.secho(f"   Namespace: {namespace}", fg=typer.colors.CYAN)
            typer.secho(f"   Pod: {pod_name}", fg=typer.colors.CYAN)
        else:
            typer.secho("❌ Vault is not accessible", fg=typer.colors.RED)
            typer.secho(f"   Check if pod {pod_name} exists in namespace {namespace}", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"❌ Error checking Vault status: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

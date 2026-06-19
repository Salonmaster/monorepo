import os
import pathlib
import typer
import asyncio
import kubernetes
import kubernetes_asyncio
import enums
import atexit
from stylist import helpers
from stylist.helpers import remote_db
import core
from stylist.helpers import kubeconfig as kubeconfig_helper

from .status import status
from .list_secrets import list_secrets
from .read_secret import read_secret
from .write_secret import write_secret
from .unseal import unseal
from .init import init

_vault_app = typer.Typer(help="Vault management commands")


@_vault_app.callback(invoke_without_command=True)
def vault(
    ctx: typer.Context,
    environment: enums.Environment = typer.Option(
        "tst",
        "--environment", "-e",
        help="The environment to use (tst, acc, prd)",
        envvar="ENV"
    ),
    kubeconfig: pathlib.Path = typer.Option(
        "~/.kube/config",
        "--kubeconfig", "-k",
        help="Path to the kubeconfig file",
        envvar="KUBECONFIG"
    ),
    secrets_db: str | None = typer.Option(
        None,
        "--secrets-db", "-s",
        help="Path to the secrets database file",
        envvar="SECRETS_DB"
    ),
    secrets_db_password: str = typer.Option(
        None,
        "--secrets-db-password", "-p",
        help="Password for the secrets database",
        envvar="SECRETS_DB_PASSWORD"
    ),
    namespace: str = typer.Option(
        "vault",
        "--namespace", "-n",
        help="Kubernetes namespace where Vault is deployed",
    ),
    pod_name: str = typer.Option(
        "vault-0",
        "--pod-name",
        help="Name of the Vault pod",
    ),
):
    """Common options for vault commands."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)
    
    core.Backbone().context.environment = environment

    kubeconfig_input = str(kubeconfig)
    kubeconfig_handle = None
    if remote_db.is_s3_path(kubeconfig_input):
        try:
            local_kubeconfig, kubeconfig_handle = kubeconfig_helper.prepare_kubeconfig(
                kubeconfig_input,
            )
        except FileNotFoundError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc
        core.Backbone().context.kubeconfig = local_kubeconfig
    else:
        core.Backbone().context.kubeconfig = os.path.expanduser(kubeconfig_input)
    core.Backbone().context.kubeconfig_handle = kubeconfig_handle
    if core.Backbone().context.kubeconfig:
        os.environ["KUBECONFIG"] = core.Backbone().context.kubeconfig
    if kubeconfig_handle:
        atexit.register(kubeconfig_handle.close)
    
    secrets_db_value = secrets_db if secrets_db else None
    if secrets_db_value and remote_db.is_s3_path(secrets_db_value):
        core.Backbone().context.secrets_db = remote_db.normalize_s3_path(secrets_db_value)
    else:
        core.Backbone().context.secrets_db = os.path.expanduser(secrets_db_value) if secrets_db_value else None
    core.Backbone().context.secrets_db_password = secrets_db_password
    core.Backbone().context.credentials = []
    
    # Store vault-specific context
    core.Backbone().context.vault_namespace = namespace
    core.Backbone().context.vault_pod_name = pod_name

    local_db, db_handle = remote_db.prepare_secrets_db(
        core.Backbone().context.secrets_db,
        auto_cleanup=False,
    )
    if db_handle:
        core.Backbone().context.secrets_db = local_db
        core.Backbone().context.secrets_db_handle = db_handle
        atexit.register(db_handle.close)

    typer.secho("🔐 Stylist Vault Context", fg=typer.colors.BRIGHT_BLUE, bold=True)
    typer.secho("───────────────────────────────", fg=typer.colors.BRIGHT_BLACK)
    typer.secho(f"✅ Environment    : {core.Backbone().context.environment.value}", fg=typer.colors.CYAN)
    typer.secho(f"📦 Namespace      : {namespace}", fg=typer.colors.CYAN)
    typer.secho(f"🏷️  Pod Name       : {pod_name}", fg=typer.colors.CYAN)
    kubeconfig_display = (
        core.Backbone().context.kubeconfig_handle.source_path
        if core.Backbone().context.kubeconfig_handle
        else core.Backbone().context.kubeconfig
    )
    typer.secho(f"📄 Kubeconfig path: {kubeconfig_display}", fg=typer.colors.CYAN)
    if core.Backbone().context.kubeconfig_handle:
        typer.secho(
            f"   ↳ Cached at: {core.Backbone().context.kubeconfig}",
            fg=typer.colors.BRIGHT_BLACK,
        )
    typer.secho("───────────────────────────────", fg=typer.colors.BRIGHT_BLACK)

    if core.Backbone().context.secrets_db:
        display_path = (
            core.Backbone().context.secrets_db_handle.source_path
            if core.Backbone().context.secrets_db_handle
            else core.Backbone().context.secrets_db
        )
        helpers.database.test_db_connection(
            db_path=str(core.Backbone().context.secrets_db),
            password=core.Backbone().context.secrets_db_password,
            display_path=display_path,
        )

    try:
        kubernetes.config.load_kube_config(config_file=core.Backbone().context.kubeconfig)
        asyncio.run(kubernetes_asyncio.config.load_kube_config(config_file=core.Backbone().context.kubeconfig))
    except Exception as e:
        typer.secho("Failed to load kubeconfig", fg=typer.colors.RED)
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)


_vault_app.command("status")(status)
_vault_app.command("list")(list_secrets)
_vault_app.command("read")(read_secret)
_vault_app.command("write")(write_secret)
_vault_app.command("unseal")(unseal)
_vault_app.command("init")(init)

core.Backbone().typer_app.add_typer(_vault_app, name="vault")

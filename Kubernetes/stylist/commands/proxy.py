import os
import typer
import base64
import pathlib
import webbrowser
import subprocess
import kubernetes
import atexit
from stylist.helpers import cluster
from stylist.helpers import kubeconfig as kubeconfig_helper
from stylist.helpers import remote_db
import core


_proxy_app = typer.Typer(help="Proxy applications to the local machine")


@_proxy_app.callback(invoke_without_command=True)
def _common(
    ctx: typer.Context,
    no_browser: bool = typer.Option(False, "--no-browser", help="Skip opening the browser"),
    kubeconfig: pathlib.Path = typer.Option(
        "~/.kube/config",
        "--kubeconfig", "-k",
        help="Path to the kubeconfig file",
        envvar="KUBECONFIG"
    ),
):
    """Common options shared across proxy commands."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)
    kubeconfig_input = str(kubeconfig)
    kubeconfig_handle = None
    if remote_db.is_s3_path(kubeconfig_input):
        try:
            local_kubeconfig, kubeconfig_handle = kubeconfig_helper.prepare_kubeconfig(kubeconfig_input)
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
    typer.secho("🔗 Initializing Kubernetes client... ", nl=False)
    try:
        kubernetes.config.load_kube_config(config_file=core.Backbone().context.kubeconfig)
        typer.secho("OK", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho("Failed", fg=typer.colors.RED)
        typer.echo(f"Reason: {e}")
        raise typer.Exit(code=1)

    core.Backbone().context.open_browser = not no_browser


def _open_browser(url):
    if "WSL_DISTRO_NAME" in os.environ:
        try:
            subprocess.run(["wslview", url], check=True)
            return
        except Exception as e:
            print("wslview failed:", e)
    # fallback to default
    webbrowser.open(url)

def _start_proxy(resource: str, namespace: str, remote_port: int, http: bool = False):
    proc = None
    try:
        typer.secho(f"🌐 Starting proxy for {resource} in namespace {namespace} on port {remote_port}... ", nl=False)
        proc, local_port = cluster.start_port_forward(resource, namespace, remote_port)
        url = f"https://localhost:{local_port}" if not http else f"http://localhost:{local_port}"
        typer.secho(f"OK, Proxied {resource} on {url}", fg=typer.colors.GREEN)
        if core.Backbone().context.open_browser:
            _open_browser(url)

        typer.secho("Press CTRL+C to stop", fg=typer.colors.BLUE)
        proc.wait()
    except KeyboardInterrupt:
        typer.secho("Proxy interrupted by user.", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho("Failed", fg=typer.colors.RED)
        typer.secho(f"Error: {e}", fg=typer.colors.RED)

    finally:
        if proc:
            proc.terminate()
            proc.wait()


@_proxy_app.command("vault")
def proxy_vault():
    """Proxy Vault UI to localhost"""
    _start_proxy("svc/vault-server", "vault", 8200, True)


@_proxy_app.command("argocd")
def proxy_argocd():
    """Proxy ArgoCD to localhost"""
    v1 = kubernetes.client.CoreV1Api()
    secret = v1.read_namespaced_secret("argocd-initial-admin-secret", "argocd")
    clear_password_b64 = secret.data.get("password")
    if clear_password_b64:
        clear_password = base64.b64decode(clear_password_b64).decode("utf-8")
        typer.secho(f"🔑 ArgoCD admin password: {clear_password}")
    else:
        typer.secho("password not found in argocd-secret.", fg=typer.colors.RED)
    _start_proxy("svc/argocd-server", "argocd", 80, True)


@_proxy_app.command("keycloak")
def proxy_keycloak():
    """Proxy Keycloak to localhost"""
    _start_proxy("svc/keycloak", "keycloak", 80)


@_proxy_app.command("dashboard")
def proxy_dashboard():
    """Proxy Kubernetes dashboard to localhost"""
    _start_proxy("svc/kubernetes-dashboard-kong-proxy", "kubernetes-dashboard", 443)


@_proxy_app.command("grafana")
def proxy_grafana():
    """Proxy Grafana to localhost"""
    _start_proxy("svc/monitoring-grafana", "monitoring", 80)


core.Backbone().typer_app.add_typer(_proxy_app, name="proxy")

import time
import json
import typer
import models
import subprocess
import kubernetes
import asyncio

def wait_for_ready(namespace="argocd", timeout=120):
    """
    Wait until all Argo CD pods are ready.
    """
    v1 = kubernetes.client.CoreV1Api()

    typer.echo("⏳ Waiting for Argo CD pods to become ready... ", nl=False)

    start = time.time()
    while time.time() - start < timeout:
        pods = v1.list_namespaced_pod(namespace=namespace)
        statuses = [
            (pod.metadata.name, pod.status.phase, all(c.ready for c in pod.status.container_statuses or []))
            for pod in pods.items
        ]

        all_ready = all(phase == "Running" and ready for _, phase, ready in statuses)

        if all_ready and statuses:
            typer.secho("OK", fg=typer.colors.GREEN)
            return

        time.sleep(3)

    typer.secho("Failed", fg=typer.colors.RED)
    typer.echo("Timeout waiting for Argo CD pods to become ready")
    typer.echo("Current pod statuses:")
    for name, phase, ready in statuses:
        status = "Ready" if ready else "Not Ready"
        typer.echo(f"  - {name}: {phase} ({status})")
    typer.echo("Please check the Argo CD pods for issues")
    raise typer.Exit(code=1)

def set_application_sync_policy(
    app: models.ArgoCDApp,
    sync_policy: str = "automated",
    self_heal: bool = False,
    prune: bool = False,
    wait: bool = True
):
    """
    Set the sync policy for an Argo CD application.
    """
    typer.echo(f"Setting sync policy for application '{app.name}'...")

    cmd = ["argocd", "app", "set", app.name, "--sync-policy", sync_policy]

    if sync_policy == "automated":
        if self_heal:
            cmd.append("--self-heal")
        if prune:
            cmd.append("--prune")

    subprocess.run(cmd, check=True)

    if wait:
        typer.echo("Waiting for application to sync...")
        subprocess.run(["argocd", "app", "wait", app.name], check=True)

async def list_applications() -> list[models.ArgoCDApp] | None:
    """
    List all Argo CD applications in the specified namespace.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "argocd", "app", "list", "--output", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return None

        # Parse the JSON output
        apps_data = json.loads(stdout)
        apps = []
        for app in apps_data:

            apps.append(models.ArgoCDApp(
                name=app["metadata"]["name"],
                cluster=app["spec"]["destination"]["server"],
                namespace=app["spec"]["destination"]["namespace"],
                project=app["spec"]["project"],
                status=app["status"]["sync"]["status"],
                health=app["status"]["health"]["status"],
                sync_policy=app.get("spec", {}).get("syncPolicy", {}).get("automated", {}).get("selfHeal", "None"),
                conditions=", ".join(c["type"] for c in app.get("status", {}).get("conditions", [])),
                repo=app["spec"]["source"]["repoURL"],
                path=app["spec"]["source"]["path"],
                target=app["spec"]["source"].get("targetRevision", "HEAD")
            ))
        return apps
    except Exception:
        return None

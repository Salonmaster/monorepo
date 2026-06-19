import core
import tasks
import console
import datetime

from .runner import run_orchestrator_console

def reset():
    """Remove Stylist-managed components from the cluster and clean state."""

    reset_orchestrator = core.TaskOrchestrator(tasks=[
        tasks.prerequisites.CheckClusterConnection(),
        tasks.prerequisites.CheckHelmAvailability(),
        tasks.cluster.SetEnvironmentTask(None),
        tasks.helm.UninstallHelmChart("argocd", "argocd"),
        tasks.helm.UninstallHelmChart("vault", "vault"),
        tasks.helm.UninstallHelmChart("monitoring", "monitoring"),
        tasks.helm.UninstallHelmChart("external-secrets", "external-secrets"),
        tasks.helm.UninstallHelmChart("cloudflare", "cloudflare"),
        tasks.helm.UninstallHelmChart("keycloak", "keycloak"),
        tasks.helm.UninstallHelmChart("database-system", "database-system"),
        tasks.helm.UninstallHelmChart("website", "website"),
        tasks.helm.UninstallHelmChart("kubernetes-dashboard", "kubernetes-dashboard"),
        tasks.cluster.ClearCustomResources(),
    ])

    if core.Backbone().context.console_mode:
        run_orchestrator_console(reset_orchestrator, "Reset")
        core.Backbone().context.program_finished = datetime.datetime.now()
    else:
        console.MainWindow(reset_orchestrator).run()

import core
import tasks
import console
import datetime

from .runner import run_orchestrator_console

def redeploy():
    """Reset the cluster and immediately bootstrap it again."""

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

    ])
    bootstrap_orchestrator = core.TaskOrchestrator(tasks=[
        tasks.prerequisites.CheckClusterConnection(),
        tasks.prerequisites.CheckClusterEmpty(),
        tasks.prerequisites.CheckHelmAvailability(),
        tasks.cluster.SetEnvironmentTask(core.Backbone().context.environment),
        tasks.cluster.InstallMonitoringCRDs(),
        tasks.argocd.InstallArgoCD(),
        tasks.vault.InstallVault(),
        tasks.vault.InitializeVault(),
        tasks.vault.UnsealVault(),
        tasks.vault.EnableV2Secrets(),
        tasks.vault.EnableKubernetesAuthentication(),
        tasks.vault.InsertSecrets(),
        tasks.external_secrets.InstallExternalSecretsOperator(),
        tasks.external_secrets.ConfigureClusterSecretsStore(),
        tasks.argocd.InstallAppOfApps(),
        tasks.argocd.WaitArgoCDReady(),
    ])
    if core.Backbone().context.console_mode:
        run_orchestrator_console(reset_orchestrator, "Reset")
        run_orchestrator_console(bootstrap_orchestrator, "Bootstrap")
        core.Backbone().context.program_finished = datetime.datetime.now()
    else:
        console.MainWindowReset(reset_orchestrator, bootstrap_orchestrator).run()

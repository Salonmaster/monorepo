import core
import tasks
import console
import datetime

from .runner import run_orchestrator_console

def bootstrap():
    """Bootstrap the selected environment with core platform services."""
    orchestrator = core.TaskOrchestrator(tasks=[
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
        # tasks.argocd.WaitArgoCDReady(),
    ])

    if core.Backbone().context.console_mode:
        run_orchestrator_console(orchestrator, "Bootstrap")
        core.Backbone().context.program_finished = datetime.datetime.now()
    else:
        console.MainWindow(orchestrator).run()

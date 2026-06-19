import os
import core
import models
from tasks.helm import InstallHelmChart
from tasks.external_secrets import ConfigureClusterSecretsStore
class InstallArgoCD(InstallHelmChart):
    def __init__(self):
        repositories = [
            models.HelmRepository(name="argo-cd", url="https://argoproj.github.io/argo-helm")
        ]
        chart_path = os.path.join(os.getcwd(), "..", "apps", "argocd")
        values_file = os.path.join(os.getcwd(), "..", "apps", "argocd", f"values-{core.Backbone().context.environment.value}.yaml")

        super().__init__(repositories,
                         chart_path,
                         values_file, "argocd", "argocd")
        self.dependencies.append(ConfigureClusterSecretsStore)




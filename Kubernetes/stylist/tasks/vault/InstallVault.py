import os
import core
import models
from tasks.helm import InstallHelmChart

class InstallVault(InstallHelmChart):
    def __init__(self):
        repositories = [
            models.HelmRepository(name="hashicorp", url="https://helm.releases.hashicorp.com")
        ]
        chart_path = os.path.join(os.getcwd(), "..", "apps", "vault")
        values_file = os.path.join(os.getcwd(), "..", "apps", "vault", f"values-{core.Backbone().context.environment.value}.yaml")

        super().__init__(repositories,
                         chart_path,
                         values_file, "vault", "vault",)

import os
import core
import models
from tasks.helm import InstallHelmChart

class InstallExternalSecretsOperator(InstallHelmChart):
    def __init__(self):
        repositories = [
            models.HelmRepository(name="external-secrets", url="https://charts.external-secrets.io")
        ]
        chart_path = os.path.join(os.getcwd(), "..", "apps", "external-secrets")
        values_file = os.path.join(os.getcwd(), "..", "apps", "external-secrets", f"values-{core.Backbone().context.environment.value}.yaml")

        super().__init__(repositories,
                         chart_path,
                         values_file, "external-secrets", "external-secrets",
                         wait_for_pods=True)

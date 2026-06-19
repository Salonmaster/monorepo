import os
import models
from stylist import helpers
from .InstallExternalSecretsOperator import InstallExternalSecretsOperator
from ..vault.EnableKubernetesAuthentication import EnableKubernetesAuthentication

class ConfigureClusterSecretsStore(models.Task):
    def __init__(self):
        super().__init__("Configure Cluster Secrets Store")
        self.dependencies = [EnableKubernetesAuthentication, InstallExternalSecretsOperator]

    async def run(self):
        # Configure namespace
        self.logger.info("Configuring Cluster Secrets Store")
        return await helpers.cluster.install_yaml_file(os.path.normpath(os.path.join(os.getcwd(), "..", "apps", "external-secrets", "cluster-secrets-store.yaml")), "external-secrets")

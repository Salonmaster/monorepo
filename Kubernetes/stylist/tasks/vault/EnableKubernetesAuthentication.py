import core
import models
import asyncio
from stylist.helpers import vault
from .UnsealVault import UnsealVault

class EnableKubernetesAuthentication(models.Task):
    def __init__(self):
        super().__init__("Enable Kubernetes authentication")
        self.dependencies = [UnsealVault]

    async def run(self):
        self.logger.info("Enabling Kubernetes authentication")
        with vault.port_forward_vault(namespace="vault", pod_name="vault-0") as vault_url:
            return await asyncio.to_thread(vault.enable_kubernetes_authentication, core.Backbone().context.vault_keys.root_token, url=vault_url)


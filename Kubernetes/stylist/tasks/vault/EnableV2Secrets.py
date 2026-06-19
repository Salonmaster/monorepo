import core
import models
import asyncio
from stylist.helpers import vault
from .UnsealVault import UnsealVault

class EnableV2Secrets(models.Task):
    def __init__(self):
        super().__init__("Enable KV V2 secrets engine")
        self.dependencies = [UnsealVault]

    async def run(self):
        self.logger.info("Enable KV V2 secrets engine")
        with vault.port_forward_vault(namespace="vault", pod_name="vault-0") as vault_url:
            return await asyncio.to_thread(vault.enable_kv_v2_secrets_engine, core.Backbone().context.vault_keys.root_token, url=vault_url)


import core
import models
import asyncio
from stylist.helpers import vault
from .InstallVault import InstallVault

class InitializeVault(models.Task):
    def __init__(self):
        super().__init__("Initialize main vault instance")
        self.dependencies = [InstallVault]
        self.delay = 10

    async def run(self) -> bool:
        self.logger.info("Waiting for Vault to be ready...")
        while not await vault.check_vault_connection():
            await asyncio.sleep(1)
        self.logger.info("Initializing Vault")
        if not (vault_keys := await vault.init_vault()):
            self.logger.error("Failed to unseal Vault.")
            return False
        core.Backbone().context.credentials.append(
            models.Credential(
                name="vault",
                fields={
                    "root_token": vault_keys.root_token,
                    **{f"unseal_key_{i}": key for i, key in enumerate(vault_keys.unseal_keys, 1)}
                }
            )
        )
        core.Backbone().context.vault_keys = vault_keys
        return True

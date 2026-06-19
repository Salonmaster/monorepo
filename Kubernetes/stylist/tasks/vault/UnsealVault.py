import core
import models
from stylist.helpers import vault
from .InitializeVault import InitializeVault

class UnsealVault(models.Task):
    def __init__(self):
        super().__init__("Unseal main vault instance")
        self.dependencies = [InitializeVault]

    async def run(self):
        self.logger.info("Unsealing Vault")
        return await vault.unseal_vault(core.Backbone().context.vault_keys)


import core
import models
import asyncio
from stylist.helpers import database, vault
from .EnableV2Secrets import EnableV2Secrets

class InsertSecrets(models.Task):
    def __init__(self):
        super().__init__("Insert secrets into KV V2")
        self.dependencies = [EnableV2Secrets]

    def process(self):
        self.logger.info("Loading secrets from database")
        secrets = database.load_secrets(
                str(core.Backbone().context.secrets_db),
                env=core.Backbone().context.environment,
                password=core.Backbone().context.secrets_db_password,
            )
        self.logger.info(f"Inserting {len(secrets)} secrets into Vault")
        with vault.port_forward_vault(namespace="vault", pod_name="vault-0") as vault_url:
            vault.store_secrets(
                secrets=secrets,
                root_token=core.Backbone().context.vault_keys.root_token,
                url=vault_url
            )

    async def run(self):
        await asyncio.to_thread(self.process)
        return True


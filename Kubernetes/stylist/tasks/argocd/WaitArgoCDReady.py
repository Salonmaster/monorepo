import asyncio
import models
from stylist import helpers
from .InstallAppOfApps import InstallAppOfApps
class WaitArgoCDReady(models.Task):
    def __init__(self):
        super().__init__("Wait for argocd to be ready")

        self.dependencies = [InstallAppOfApps]

    async def run(self):
        self.logger.info("Waiting for ArgoCD to be ready")
        done = False
        while not done:
            applications: list[models.ArgoCDApp] = await helpers.argocd.list_applications()
            if applications:
                for application in applications:
                    self.logger.info(f"Application {application.name} is {application.status}")
            else:
                self.logger.info("No applications found or failed to list applications")
            await asyncio.sleep(1)

import os
import models
from stylist import helpers
from .InstallArgoCD import InstallArgoCD
class InstallAppOfApps(models.Task):
    def __init__(self):
        super().__init__("Install app of apps")
        self.dependencies = [InstallArgoCD]

    async def run(self):
        # Configure namespace
        self.logger.info("Installing app of apps")
        app_of_apps = os.path.join(os.getcwd(), "..", "app-of-apps", "app-of-apps.yaml")
        return await helpers.cluster.install_yaml_file(app_of_apps, "argocd")

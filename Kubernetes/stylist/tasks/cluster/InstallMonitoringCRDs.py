import models
from stylist import helpers

class InstallMonitoringCRDs(models.Task):
    def __init__(self):
        super().__init__("Install Monitoring CRDs")

    async def run(self):
        # Configure namespace
        self.logger.info("Checking if monitoring namespace exists")
        if not await helpers.cluster.check_namespace_exists("monitoring"):
            self.logger.info("Monitoring namespace does not exist, creating it")
            if not await helpers.cluster.create_namespace("monitoring"):
                self.logger.info("Failed to create monitoring namespace")
                return False
        else:
            self.logger.info("Monitoring namespace already exists")
            return False

        self.logger.info("Installing monitoring CRDs")
        return await helpers.cluster.install_yaml_file("https://github.com/prometheus-operator/prometheus-operator/releases/download/v0.84.0/bundle.yaml")

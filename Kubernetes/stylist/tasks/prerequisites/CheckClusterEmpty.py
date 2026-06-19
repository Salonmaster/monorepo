import models
from stylist.helpers import cluster
from .CheckClusterConnection import CheckClusterConnection

class CheckClusterEmpty(models.Task):
    def __init__(self):
        super().__init__("Check cluster empty")
        self.dependencies = [CheckClusterConnection]

    async def run(self) -> bool:
        self.logger.info("Checking if cluster is empty")
        return not await cluster.is_cluster_configured()

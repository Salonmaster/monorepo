import models
from stylist.helpers import cluster

class CheckClusterConnection(models.Task):
    def __init__(self):
        super().__init__("Check cluster connection")

    async def run(self) -> bool:
        self.logger.info("Checking cluster connection")
        return await cluster.check_cluster_connection()

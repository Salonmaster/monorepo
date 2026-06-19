import enums
import models
from stylist import helpers
import tasks.prerequisites

class SetEnvironmentTask(models.Task):
    def __init__(self,environment: enums.Environment):
        super().__init__("Set cluster environment")
        self.environment = environment
        self.dependencies = [tasks.prerequisites.CheckClusterEmpty]

    async def run(self):
        # Logic to set the environment
        self.logger.info(f"Setting cluster environment to: {self.environment.value}" if self.environment else "Resetting cluster environment")
        if await helpers.cluster.fetch_cluster_environment() != self.environment:
            return await helpers.cluster.set_cluster_environment(self.environment)
        return True

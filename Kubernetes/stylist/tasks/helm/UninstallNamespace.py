import models
from stylist import helpers
from tasks.prerequisites import CheckHelmAvailability, CheckClusterConnection

class UninstallHelmChart(models.Task):
    def __init__(self,
                 namespace: str,
                 release_name: str):
        super().__init__(f"Uninstall Helm Chart: {release_name}")
        self.namespace = namespace
        self.release_name = release_name
        self.dependencies = [CheckHelmAvailability, CheckClusterConnection]

    async def run(self) -> bool:
        self.logger.info("Checking if namespace exists")

        self.logger.info("Uninstalling Helm chart")
        if not await helpers.helm.uninstall_chart(self.release_name, self.namespace):
            self.logger.warning("Failed to uninstall Helm chart")

        if not await helpers.cluster.check_namespace_exists(self.namespace):
            self.logger.info(f"Namespace '{self.namespace}' does not exist")
        else:
            self.logger.info("Removing namespace")
            if not await helpers.cluster.delete_namespace(self.namespace, timeout=30):
                self.logger.warning("Failed to remove namespace, dropping finalizers")
                if not await helpers.cluster.delete_namespace(self.namespace, timeout=60, force=True):
                    self.logger.warning("Failed to remove namespace")
                    return False

        self.logger.info("Removing PVCs in the namespace")
        await helpers.cluster.delete_namespace_pvcs(self.namespace)
        return True

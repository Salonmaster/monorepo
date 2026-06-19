import models
from stylist.helpers import helm

class CheckHelmAvailability(models.Task):
    def __init__(self):
        super().__init__("Check helm availability")
        self.retries = 0

    async def run(self) -> bool:
        self.logger.info("Checking if Helm is installed and available in PATH")
        return await helm.check_helm_availability()

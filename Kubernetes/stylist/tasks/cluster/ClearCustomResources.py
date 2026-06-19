import models
from stylist import helpers


class ClearCustomResources(models.Task):
    def __init__(self):
        super().__init__("Remove Custom Resources")

    async def run(self) -> bool:
        self.logger.info("Deleting all custom resources and CRDs")
        attempts = 0
        last_remaining: list[str] = []
        while attempts < 3:
            attempts += 1
            await helpers.cluster.delete_all_custom_resources()
            cleared, remaining = await helpers.cluster.wait_for_crd_terminations(timeout=300)
            if cleared:
                return True
            last_remaining = remaining
            if remaining:
                self.logger.warning(
                    "Attempt %s: CRDs still terminating (%s); forcing another cleanup cycle",
                    attempts,
                    ", ".join(remaining),
                )
                # Force cleanup of remaining CRDs
                await helpers.cluster.force_delete_custom_resources(remaining)
                await helpers.cluster.force_remove_crd_finalizers(remaining, logger=self.logger)
                for crd_name in remaining:
                    await helpers.cluster.force_delete_crd(crd_name, logger=self.logger)
        if last_remaining:
            self.logger.error(
                "Failed to remove CRDs after forced cleanup: %s",
                ", ".join(last_remaining),
            )
        return False

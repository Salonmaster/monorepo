import asyncio
import models
from stylist import helpers
from tasks.prerequisites import CheckHelmAvailability, CheckClusterConnection

class InstallHelmChart(models.Task):
    def __init__(self,
                 repositories: list[models.HelmRepository],
                 path: str,
                 values_file: str,
                 namespace: str,
                 release_name: str,
                 wait_for_pods: bool = True):
        super().__init__(f"Install Helm Chart: {release_name}")
        self.repositories = repositories
        self.path = path
        self.namespace = namespace
        self.release_name = release_name
        self.values_file = values_file
        self.wait_for_pods = wait_for_pods
        self.dependencies = [CheckHelmAvailability, CheckClusterConnection]

    async def configure_repositories(self) -> bool:
        self.logger.info("Configuring repositories")
        helm_repositories: list[models.HelmRepository] = await helpers.helm.get_configured_repositories()
        helm_repo_dict = {repo.name: repo.url for repo in helm_repositories}
        missing_repositories = [repo for repo in self.repositories if repo.name not in helm_repo_dict or helm_repo_dict[repo.name] != repo.url]



        for repo in missing_repositories:
            self.logger.info(f"Updating Helm repository '{repo.name}' URL from '{helm_repo_dict.get(repo.name, 'unknown')}' to '{repo.url}'")
            if not await helpers.helm.add_helm_repo(repo):
                self.logger.info(f"Failed to update Helm repository '{repo.name}'")
                return False
        return True

    async def run(self) -> bool:
        if await helpers.cluster.check_namespace_exists(self.namespace):
            self.logger.info(f"Namespace '{self.namespace}' already exists")
            return False

        if not await self.configure_repositories():
            return False

        self.logger.info("Ensuring no CRDs are still terminating")
        crd_cleared, terminating = await helpers.cluster.wait_for_crd_terminations(timeout=30)
        if not crd_cleared:
            crd_list = ", ".join(terminating) if terminating else "unknown"
            self.logger.warning(
                "Timed out waiting for CRDs to finish deleting (stuck: %s); attempting cleanup",
                crd_list,
            )
            # Retry loop for aggressive cleanup
            max_retries = 5
            for attempt in range(max_retries):
                if terminating:
                    # First, delete all custom resources that use these CRDs
                    await helpers.cluster.force_delete_custom_resources(terminating)
                    # Remove finalizers from CRDs
                    await helpers.cluster.force_remove_crd_finalizers(terminating, logger=self.logger)
                    # Force delete the CRDs themselves
                    for crd_name in terminating:
                        await helpers.cluster.force_delete_crd(crd_name, logger=self.logger)
                    # Wait a bit for Kubernetes to process
                    await asyncio.sleep(3)
                    # Check if CRDs are gone
                    crd_cleared, terminating = await helpers.cluster.wait_for_crd_terminations(timeout=30)
                    if crd_cleared:
                        break
                    if attempt < max_retries - 1:
                        self.logger.info(
                            f"Retry {attempt + 1}/{max_retries}: CRDs still terminating, retrying cleanup"
                        )
        if not crd_cleared:
            self.logger.warning("CRDs still terminating after remediation; aborting install")
            return False

        self.logger.info("Building Helm chart dependencies")
        if not await helpers.helm.dependency_build(self.path):
            self.logger.info("Failed to build Helm chart dependencies")
            return False

        self.logger.info("Installing Helm chart")
        if not await helpers.helm.install_chart(self.path, self.release_name, self.namespace, self.values_file):
            self.logger.info("Failed to install Helm chart")
            return False

        if self.wait_for_pods:
            self.logger.info("Waiting for pods to start")
            await helpers.cluster.wait_for_all_pods_ready(self.namespace, timeout=300)
            await helpers.cluster.wait_for_all_deployments_ready(self.namespace, timeout=300)
        return True

import yaml
import time
import json
import enums
import typer
import asyncio
import kubernetes
import kubernetes_asyncio
import subprocess
import socket
import pathlib
import logging

def get_ca_cert() -> str | None:
    """
    Fetch the Kubernetes CA certificate from the cluster.
    Returns the CA certificate as a string or None if not found.
    """

    import time


    core = kubernetes.client.CoreV1Api()

    # Define the pod
    pod_manifest = kubernetes.client.V1Pod(
        metadata=kubernetes.client.V1ObjectMeta(name="cert-fetcher"),
        spec=kubernetes.client.V1PodSpec(
            restart_policy="Never",
            containers=[
                kubernetes.client.V1Container(
                    name="alpine",
                    image="alpine",
                    command=["sh", "-c"],
                    args=["apk add openssl > /dev/null && "
                        "echo | openssl s_client -connect kubernetes.default.svc:443 -showcerts 2>/dev/null "
                        "| awk '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/ { print } NR>1 && /-----END CERTIFICATE-----/ { exit }'"]
                )
            ],
        )
    )

    # Create the pod
    core.create_namespaced_pod(namespace="default", body=pod_manifest)

    # Wait for pod to finish
    while True:
        pod_status = core.read_namespaced_pod(name="cert-fetcher", namespace="default")
        phase = pod_status.status.phase
        if phase in ["Succeeded", "Failed"]:
            break
        time.sleep(1)

    # Get logs (output of the command)
    ca_cert = core.read_namespaced_pod_log(name="cert-fetcher", namespace="default")

    # Clean up
    core.delete_namespaced_pod(name="cert-fetcher", namespace="default", body=kubernetes.client.V1DeleteOptions())
    return ca_cert.strip() if ca_cert else None


async def check_cluster_connection() -> bool:
    """
    Check if the connection to the Kubernetes cluster is successful.
    Returns True if connected, False otherwise.
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)

        try:
            await v1.list_namespace()
            return True
        except Exception:
            return False


async def install_yaml_file(file_path: str, namespace: str = "default") -> bool:
    """
    Install a YAML file using kubectl apply.

    Args:
        file_path (str): The path to the YAML file to install.
        namespace (str): The namespace where the resources will be installed (ignored for cluster-wide).
    """
    result = await asyncio.create_subprocess_exec(
        "kubectl", "apply", "--server-side", "-f", file_path, "-n", namespace,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await result.communicate()
    if await result.wait() == 0:
        return True

    # Surface kubectl output to aid debugging when the apply fails.
    if stdout:
        typer.echo(stdout.decode().strip())
    if stderr:
        typer.secho(stderr.decode().strip(), fg=typer.colors.RED)
    return False


def remove_yaml_file(file_path: str, namespace: str = "default") -> None:
    """
    Remove a YAML file using kubectl delete.

    Args:
        file_path (str): The path to the YAML file to remove.
        namespace (str): The namespace where the resources will be removed (ignored for cluster-wide).
    """
    typer.echo(f"🗑️  Removing resources from '{file_path}' in namespace '{namespace}'... ", nl=False)

    try:
        subprocess.run(
            ["kubectl", "delete", "-f", file_path, "-n", namespace],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        typer.secho("OK", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError:
        typer.secho("Failed", fg=typer.colors.RED)

async def check_namespace_exists(namespace: str) -> bool:
    """Check if the specified namespace exists in the cluster.
    Args:
        namespace (str): The namespace to check.
    Returns:
        bool: True if the namespace exists, False otherwise.
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        try:
            await v1.read_namespace(name=namespace)
            return True
        except kubernetes_asyncio.client.rest.ApiException:
            return False

async def create_namespace(namespace: str) -> bool:
    """Create a namespace in the cluster if it does not exist.
    Args:
        namespace (str): The namespace to create.
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        ns_body = kubernetes_asyncio.client.V1Namespace(metadata=kubernetes_asyncio.client.V1ObjectMeta(name=namespace))

        try:
            await v1.create_namespace(body=ns_body)
            return True
        except kubernetes_asyncio.client.rest.ApiException as e:
            if e.status == 409:  # Conflict, namespace already exists
                return False
            return False

async def delete_namespace(namespace: str, wait: bool = True, timeout: int = 60, force: bool = True) -> bool:
    """
    Delete a namespace from the cluster, optionally removing finalizers if needed.

    Args:
        namespace (str): The namespace to delete.
        wait (bool): Whether to wait until it's fully deleted.
        timeout (int): How long to wait before giving up (in seconds).
        force (bool): Whether to remove finalizers if deletion gets stuck.
    """

    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        try:
            # First try deleting normally
            await v1.delete_namespace(
                name=namespace,
                body=kubernetes_asyncio.client.V1DeleteOptions(grace_period_seconds=0)
            )
        except kubernetes_asyncio.client.rest.ApiException as e:
            if e.status == 404:
                return True  # Namespace already deleted
            return False

        # Optionally wait for deletion
        start = time.time()
        while wait:
            try:
                await v1.read_namespace(name=namespace)
                if time.time() - start > timeout:
                    if force:
                        await force_remove_namespace_finalizers(namespace)
                        return True
                    return False
                await asyncio.sleep(1)
            except kubernetes_asyncio.client.rest.ApiException as e:
                if e.status == 404:
                    break
                raise

    return True

async def force_remove_namespace_finalizers(namespace: str):
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        # Get full namespace object
        ns = await kubernetes_asyncio.client.CoreV1Api(api_client).read_namespace(name=namespace, _preload_content=False)
        ns_obj = json.loads(await ns.text())

        # Remove finalizers
        ns_obj['spec']['finalizers'] = []

        # PUT to /finalize
        response = await api_client.call_api(
            f'/api/v1/namespaces/{namespace}/finalize',
            'PUT',
            body=ns_obj,
            auth_settings=['BearerToken'],
            _preload_content=False
        )

    return response.ok

async def set_cluster_environment(environment: enums.Environment | None) -> bool:
    """
    Set or remove the cluster environment by managing the ConfigMap.
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        name = "cluster-environment"
        namespace = "kube-system"  # Consider switching to "stylist-system"

        if not environment:
            try:
                await v1.delete_namespaced_config_map(name=name, namespace=namespace)
                return True
            except Exception:
                return False

        cm_data = {"environment": environment.value}
        cm_body = kubernetes_asyncio.client.V1ConfigMap(
            metadata=kubernetes_asyncio.client.V1ObjectMeta(name=name, namespace=namespace),
            data=cm_data
        )

        try:
            # Try to replace (update) it if it exists
            await v1.replace_namespaced_config_map(name=name, namespace=namespace, body=cm_body)
            return True
        except Exception as e:
            if getattr(e, "status", None) == 404:
                try:
                    await v1.create_namespaced_config_map(namespace=namespace, body=cm_body)
                    return True
                except Exception:
                    return False
            else:
                return False

async def fetch_cluster_environment() -> enums.Environment | None:
    """
    Fetch the current cluster environment from a ConfigMap in the cluster.
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        try:
            cm = await v1.read_namespaced_config_map(
                name="cluster-environment",
                namespace="kube-system"  # or wherever you put it
            )
        except Exception:
            return None
        env_value = cm.data.get("environment", "").strip()
        return enums.Environment(env_value)


async def is_cluster_configured() -> bool:
    """
    Ensure the cluster is not configured by checking if the environment is set.
    Raises an error if the environment is already set.
    """
    return await fetch_cluster_environment() is not None

async def wait_for_namespace_creation(namespace: str, timeout: int = 120) -> None:
    """
    Wait for the namespace to be created.

    Args:
        namespace (str): The namespace to check.
        timeout (int): The maximum time to wait for the namespace to be created (in seconds).
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)

        start_time = time.time()
        while True:
            try:
                await v1.read_namespace(name=namespace)
                typer.secho("OK", fg=typer.colors.GREEN)
                break
            except kubernetes_asyncio.client.rest.ApiException as e:
                if e.status == 404:
                    pass  # Namespace not found, continue waiting
                else:
                    return
            if time.time() - start_time > timeout:
                break
            await asyncio.sleep(1)  # Check every 1 second

async def wait_for_crd_terminations(
    timeout: int = 120,
    poll_interval: float = 2.0,
) -> tuple[bool, list[str]]:
    """Wait until there are no CustomResourceDefinitions stuck terminating."""
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        api = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
        start_time = time.time()
        while True:
            crds = await api.list_custom_resource_definition()
            terminating = [
                crd.metadata.name
                for crd in crds.items
                if getattr(crd.metadata, "deletion_timestamp", None) is not None
            ]
            if not terminating:
                return True, []
            if time.time() - start_time > timeout:
                return False, sorted(terminating)
            await asyncio.sleep(poll_interval)


async def force_remove_crd_finalizers(crd_names: list[str], logger: logging.Logger | None = None) -> bool:
    """Clear finalizers from CRDs stuck in Terminating state."""
    if not crd_names:
        return True
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        api = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
        overall_success = True
        for name in crd_names:
            patch_body = {"metadata": {"finalizers": []}}
            try:
                await api.patch_custom_resource_definition(
                    name=name,
                    body=patch_body,
                )
                if logger:
                    logger.warning(f"Removed finalizers from CRD '{name}' to unblock deletion")
                else:
                    typer.secho(
                        f"Removed finalizers from CRD '{name}' to unblock deletion",
                        fg=typer.colors.YELLOW,
                    )
            except Exception as exc:  # pragma: no cover - best-effort cleanup
                overall_success = False
                if logger:
                    logger.error(f"Failed to remove finalizers from CRD '{name}': {exc}")
                else:
                    typer.secho(
                        f"Failed to remove finalizers from CRD '{name}': {exc}",
                        fg=typer.colors.RED,
                    )
        return overall_success


async def force_delete_crd(crd_name: str, logger: logging.Logger | None = None) -> bool:
    """Force delete a CRD by removing finalizers and deleting it directly using kubectl."""
    # First, always remove finalizers via API before attempting deletion
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        api = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
        try:
            crd = await api.read_custom_resource_definition(crd_name)
            # Remove finalizers if they exist
            if crd.metadata.finalizers:
                patch_body = {"metadata": {"finalizers": []}}
                await api.patch_custom_resource_definition(
                    name=crd_name,
                    body=patch_body,
                )
                if logger:
                    logger.warning(f"Removed finalizers from CRD '{crd_name}' to unblock deletion")
                await asyncio.sleep(1)  # Wait for Kubernetes to process
        except kubernetes_asyncio.client.rest.ApiException as exc:
            if exc.status == 404:
                # CRD doesn't exist, consider it deleted
                if logger:
                    logger.info(f"CRD '{crd_name}' does not exist, already deleted")
                return True
            # If it's not 404, log but continue with deletion attempt
            if logger:
                logger.debug(f"Could not read/patch CRD '{crd_name}': {exc}")
    
    # Now try using kubectl for more aggressive deletion
    try:
        # Use kubectl delete with --force and --grace-period=0
        process = await asyncio.create_subprocess_exec(
            "kubectl",
            "delete",
            "crd",
            crd_name,
            "--force",
            "--grace-period=0",
            "--ignore-not-found=true",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        stderr_text = stderr.decode() if stderr else ""
        
        # Also try API-based deletion as a backup
        async with kubernetes_asyncio.client.ApiClient() as api_client:
            api = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
            delete_opts = kubernetes_asyncio.client.V1DeleteOptions(
                grace_period_seconds=0,
                propagation_policy="Background",
            )
            try:
                await api.delete_custom_resource_definition(
                    name=crd_name,
                    body=delete_opts,
                )
            except kubernetes_asyncio.client.rest.ApiException as exc:
                if exc.status != 404:
                    if logger:
                        logger.debug(f"API delete also failed for CRD '{crd_name}': {exc}")
            
            # Wait and verify deletion with multiple checks
            max_checks = 15
            for check_num in range(max_checks):
                await asyncio.sleep(1)
                try:
                    await api.read_custom_resource_definition(crd_name)
                    # Still exists, continue checking
                except kubernetes_asyncio.client.rest.ApiException as exc:
                    if exc.status == 404:
                        # CRD is deleted
                        if logger:
                            logger.warning(f"Force deleted CRD '{crd_name}'")
                        else:
                            typer.secho(
                                f"Force deleted CRD '{crd_name}'",
                                fg=typer.colors.YELLOW,
                            )
                        return True
                    raise
            
            # If we get here, CRD still exists after deletion attempt
            if logger:
                logger.warning(f"CRD '{crd_name}' deletion initiated but may still be terminating")
            else:
                typer.secho(
                    f"CRD '{crd_name}' deletion initiated but may still be terminating",
                    fg=typer.colors.YELLOW,
                )
            return True
    except Exception as kubectl_exc:
        # Fallback to API-based deletion if kubectl fails
        if logger:
            logger.debug(f"kubectl force delete failed for '{crd_name}', trying API method: {kubectl_exc}")
        
        async with kubernetes_asyncio.client.ApiClient() as api_client:
            api = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
            try:
                # First, check if CRD exists
                try:
                    crd = await api.read_custom_resource_definition(crd_name)
                except kubernetes_asyncio.client.rest.ApiException as exc:
                    if exc.status == 404:
                        # CRD doesn't exist, consider it deleted
                        if logger:
                            logger.info(f"CRD '{crd_name}' does not exist, already deleted")
                        return True
                    raise
                
                # Remove finalizers if they exist
                if crd.metadata.finalizers:
                    patch_body = {"metadata": {"finalizers": []}}
                    await api.patch_custom_resource_definition(
                        name=crd_name,
                        body=patch_body,
                    )
                    # Wait a moment for Kubernetes to process the finalizer removal
                    await asyncio.sleep(1)
                
                # Force delete the CRD with grace period 0 and background propagation
                delete_opts = kubernetes_asyncio.client.V1DeleteOptions(
                    grace_period_seconds=0,
                    propagation_policy="Background",
                )
                try:
                    await api.delete_custom_resource_definition(
                        name=crd_name,
                        body=delete_opts,
                    )
                except kubernetes_asyncio.client.rest.ApiException as exc:
                    # If it's already gone (404), that's fine
                    if exc.status != 404:
                        raise
                
                # Verify deletion by checking if CRD still exists
                max_checks = 10
                for _ in range(max_checks):
                    await asyncio.sleep(0.5)
                    try:
                        await api.read_custom_resource_definition(crd_name)
                    except kubernetes_asyncio.client.rest.ApiException as exc:
                        if exc.status == 404:
                            # CRD is deleted
                            if logger:
                                logger.warning(f"Force deleted CRD '{crd_name}'")
                            else:
                                typer.secho(
                                    f"Force deleted CRD '{crd_name}'",
                                    fg=typer.colors.YELLOW,
                                )
                            return True
                
                # If we get here, CRD still exists after deletion attempt
                if logger:
                    logger.warning(f"CRD '{crd_name}' deletion initiated but may still be terminating")
                else:
                    typer.secho(
                        f"CRD '{crd_name}' deletion initiated but may still be terminating",
                        fg=typer.colors.YELLOW,
                    )
                return True
            except Exception as exc:
                if logger:
                    logger.error(f"Failed to force delete CRD '{crd_name}': {exc}")
                else:
                    typer.secho(
                        f"Failed to force delete CRD '{crd_name}': {exc}",
                        fg=typer.colors.RED,
                    )
                return False


async def _force_delete_custom_object(
    api: kubernetes_asyncio.client.CustomObjectsApi,
    group: str,
    version: str,
    plural: str,
    name: str,
    namespace: str | None,
) -> None:
    patch_body = {"metadata": {"finalizers": []}}
    try:
        if namespace:
            await api.patch_namespaced_custom_object(group, version, namespace, plural, name, patch_body)
        else:
            await api.patch_cluster_custom_object(group, version, plural, name, patch_body)
    except Exception:
        pass

    delete_opts = kubernetes_asyncio.client.V1DeleteOptions(
        grace_period_seconds=0,
        propagation_policy="Background",
    )
    try:
        if namespace:
            await api.delete_namespaced_custom_object(
                group,
                version,
                namespace,
                plural,
                name,
                body=delete_opts,
            )
        else:
            await api.delete_cluster_custom_object(
                group,
                version,
                plural,
                name,
                body=delete_opts,
            )
    except kubernetes_asyncio.client.rest.ApiException as exc:  # pragma: no cover - best-effort cleanup
        if exc.status != 404:
            typer.secho(
                f"Failed to delete custom resource {plural}/{name}: {exc}",
                fg=typer.colors.RED,
            )


async def force_delete_custom_resources(crd_names: list[str]) -> None:
    if not crd_names:
        return
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        apiext = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
        custom_api = kubernetes_asyncio.client.CustomObjectsApi(api_client)
        for crd_name in crd_names:
            try:
                crd = await apiext.read_custom_resource_definition(crd_name)
            except Exception as exc:  # pragma: no cover - informational
                typer.secho(
                    f"Unable to inspect CRD '{crd_name}' while forcing deletion: {exc}",
                    fg=typer.colors.RED,
                )
                continue
            group = crd.spec.group
            plural = crd.spec.names.plural
            scope = crd.spec.scope or "Cluster"
            versions = [ver.name for ver in crd.spec.versions if ver.served]
            for version in versions:
                try:
                    resources = await custom_api.list_cluster_custom_object(group, version, plural)
                except Exception as exc:
                    typer.secho(
                        f"Failed to list {plural} for CRD '{crd_name}': {exc}",
                        fg=typer.colors.RED,
                    )
                    continue
                for item in resources.get("items", []):
                    namespace = item.get("metadata", {}).get("namespace") if scope == "Namespaced" else None
                    name = item.get("metadata", {}).get("name")
                    if not name:
                        continue
                    await _force_delete_custom_object(
                        custom_api,
                        group,
                        version,
                        plural,
                        name,
                        namespace,
                    )


async def list_all_crd_names(exclude: set[str] | None = None) -> list[str]:
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        apiext = kubernetes_asyncio.client.ApiextensionsV1Api(api_client)
        crds = await apiext.list_custom_resource_definition()
        names: list[str] = []
        for crd in crds.items:
            name = crd.metadata.name
            if exclude and name in exclude:
                continue
            names.append(name)
        return names


async def delete_all_custom_resources(exclude: set[str] | None = None) -> None:
    crd_names = await list_all_crd_names(exclude)
    if not crd_names:
        return
    await force_delete_custom_resources(crd_names)
    await force_remove_crd_finalizers(crd_names)

async def wait_for_all_pods_ready(namespace: str, timeout: int = 120) -> None:
    """Wait for all pods in the specified namespace to be ready.
    Args:
        namespace (str): The namespace to check.
        timeout (int): The maximum time to wait for all pods to be ready (in seconds).
    """

    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)

        start_time = time.time()
        while True:
            pods = await v1.list_namespaced_pod(namespace=namespace)
            if all(pod.status.phase == "Running" and pod.status.conditions[0].status == "True" for pod in pods.items):
                return True
            if time.time() - start_time > timeout:
                return False
            await asyncio.sleep(0.1)  # Check every 1 second

async def wait_for_all_deployments_ready(namespace: str, timeout: int = 120) -> None:
    """Wait for all deployments in the specified namespace to be ready.
    Args:
        namespace (str): The namespace to check.
        timeout (int): The maximum time to wait for all deployments to be ready (in seconds).
    """
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        apps_v1 = kubernetes_asyncio.client.AppsV1Api(api_client)

        start_time = time.time()
        while True:
            deployments = await apps_v1.list_namespaced_deployment(namespace=namespace)
            if all(deployment.status.ready_replicas == deployment.status.replicas for deployment in deployments.items):
                return True
            if time.time() - start_time > timeout:
                return False
            await asyncio.sleep(0.1)  # Check every 1 second

async def get_pods_by_label(label_selector: str, namespace: str) -> list[str]:
    """Get the names of pods by their label selector in the specified namespace.
    Args:
        label_selector (str): The label selector to filter pods.
        namespace (str): The namespace to search in.
    Returns:
        str: The name of the first pod that matches the label selector.
    """
    v1 = kubernetes.client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector).items
    if not pods:
        raise ValueError(f"No pods found with label '{label_selector}' in namespace '{namespace}'")
    return [pod.metadata.name for pod in pods]


def start_port_forward(resource: str, namespace: str, remote_port: int) -> tuple[subprocess.Popen, int]:
    """Start a port-forward to a Kubernetes resource and return the process and local port."""
    sock = socket.socket()
    sock.bind(("", 0))
    local_port = sock.getsockname()[1]
    sock.close()

    cmd = [
        "kubectl",
        "port-forward",
        resource,
        f"{local_port}:{remote_port}",
        "-n",
        namespace,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timeout = 5  # seconds
    start_time = time.time()
    while True:
        try:
            with socket.create_connection(("localhost", local_port), timeout=1):
                break
        except (socket.error, socket.timeout):
            if time.time() - start_time > timeout:
                proc.terminate()
                raise RuntimeError(f"Port-forward to {resource} on port {remote_port} failed to become ready within {timeout} seconds")
        time.sleep(0.5)  # Retry every 0.5 seconds
    return proc, local_port

async def delete_namespace_pvcs(namespace: str) -> bool:
    """Delete all PVCs in the specified namespace."""
    try:
        result = await asyncio.create_subprocess_exec(
            "kubectl", "delete", "pvc", "--all", "-n", namespace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
        await result.stdout.read()
        return result.returncode == 0
    except Exception:
        return False

def delete_cluster_role(name: str) -> None:
    """Delete a cluster role if it exists using kubectl."""
    try:
        subprocess.run(
            ["kubectl", "delete", "clusterrole", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        typer.secho(f"🗑️ Deleted cluster role '{name}'.", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError as e:
        if "NotFound" in e.stderr:
            typer.secho(f"🗑️ Could not find cluster role '{name}' for deletion.", fg=typer.colors.GREEN)
        else:
            typer.secho(f"🗑️ Failed to delete cluster role '{name}' for deletion.", fg=typer.colors.GREEN)

            typer.secho("Failed", fg=typer.colors.RED)
            typer.echo(e.stderr)


def delete_cluster_role_binding(name: str) -> None:
    """Delete a cluster role binding if it exists using kubectl."""
    try:
        subprocess.run(
            ["kubectl", "delete", "clusterrolebinding", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        typer.secho("OK", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError as e:
        if "NotFound" in e.stderr:
            typer.secho("Not found", fg=typer.colors.YELLOW)
        else:
            typer.secho("Failed", fg=typer.colors.RED)
            typer.echo(e.stderr)

def delete_mutating_webhook_configuration(name: str) -> None:
    """Delete a cluster mutating webhook configuration if it exists using kubectl."""
    try:
        subprocess.run(
            ["kubectl", "delete", "mutatingwebhookconfiguration", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        typer.secho("OK", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError as e:
        if "NotFound" in e.stderr:
            typer.secho("Not found", fg=typer.colors.YELLOW)
        else:
            typer.secho("Failed", fg=typer.colors.RED)
            typer.echo(e.stderr)


def get_sa_token_via_kubectl(
    service_account: str = "external-secrets",
    namespace: str = "external-secrets",
    expiration_seconds: int = 3600
) -> str:
    """
    Generates a token for a given ServiceAccount using `kubectl create token`.
    """
    typer.secho(f"🔐 Creating token for ServiceAccount '{service_account}' in namespace '{namespace}'... ", nl=False)

    try:
        result = subprocess.run(
            [
                "kubectl", "create", "token", service_account,
                "-n", namespace,
                f"--duration={expiration_seconds}s",
            ],
            capture_output=True,
            check=True,
            text=True
        )
        token = result.stdout.strip()
        typer.secho("OK", fg=typer.colors.GREEN)
        return token

    except subprocess.CalledProcessError as e:
        typer.secho("Failed", fg=typer.colors.RED)
        typer.echo(f"stderr: {e.stderr.strip()}")
        raise typer.Exit(code=1)


def get_nodes_status() -> list[tuple[str, bool]]:
    """Return readiness status for each node in the cluster."""
    v1 = kubernetes.client.CoreV1Api()
    nodes = v1.list_node().items
    status = []
    for node in nodes:
        ready = False
        for condition in node.status.conditions:
            if condition.type == "Ready":
                ready = condition.status == "True"
                break
        status.append((node.metadata.name, ready))
    return status


def get_cluster_info() -> dict:
    """Fetch basic static information about the cluster."""
    v1 = kubernetes.client.CoreV1Api()
    version = kubernetes.client.VersionApi().get_code().git_version
    env = fetch_cluster_environment()
    return {
        "version": version,
        "environment": env,
        "nodes": [n.metadata.name for n in v1.list_node().items],
    }


def list_app_names() -> list[str]:
    """Return the names of all apps under the repository's apps directory."""
    apps_dir = pathlib.Path(__file__).resolve().parents[2] / "apps"
    return sorted(p.name for p in apps_dir.iterdir() if p.is_dir())


def get_chart_version(app_name: str) -> str:
    """Return the Helm chart version for the given app."""
    chart_file = pathlib.Path(__file__).resolve().parents[2] / "apps" / app_name / "Chart.yaml"
    if chart_file.exists():
        with open(chart_file, "r") as f:
            data = yaml.safe_load(f)
        return data.get("version", "unknown")
    return "unknown"


def get_namespace_services(namespace: str) -> list[str]:
    """Return a list of service names in the given namespace."""
    v1 = kubernetes.client.CoreV1Api()
    return [svc.metadata.name for svc in v1.list_namespaced_service(namespace=namespace).items]


def get_deployment_issues(namespace: str) -> list[str]:
    """Return a list of deployment issue strings for the namespace."""
    apps_v1 = kubernetes.client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace).items
    issues = []
    for d in deployments:
        desired = d.spec.replicas or 0
        ready = d.status.ready_replicas or 0
        if ready < desired:
            issues.append(f"{d.metadata.name} not ready ({ready}/{desired} replicas)")
        if d.status.conditions:
            for cond in d.status.conditions:
                if cond.type == "Progressing" and cond.status == "False":
                    issues.append(f"{d.metadata.name}: {cond.reason}")
                if cond.type == "Available" and cond.status == "False":
                    issues.append(f"{d.metadata.name}: {cond.reason}")
    return issues


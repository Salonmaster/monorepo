import re
import models
import kubernetes_asyncio
import hvac
import socket
import subprocess
import time
from contextlib import contextmanager

async def check_vault_connection():
    try:
        async with kubernetes_asyncio.stream.WsApiClient() as api_client:
            core_v1 = kubernetes_asyncio.client.CoreV1Api(api_client=api_client)

            exec_command = [
                "/bin/sh",
                "-c",
                "vault status"
            ]


            await core_v1.connect_get_namespaced_pod_exec (
                "vault-0",
                "vault",
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            return True
    except Exception:
        return False

async def unseal_vault(vault_keys: models.VaultKeys, namespace: str = "vault", pod_name: str = "vault-0") -> bool:
    """
    Unseal the vault using the provided unseal keys.
    This function sends the unseal keys to the Vault pod to unseal it.
    """
    async with kubernetes_asyncio.stream.WsApiClient() as api_client:
        core_v1 = kubernetes_asyncio.client.CoreV1Api(api_client=api_client)

        exec_command = [
            "/bin/sh",
            "-c",
            " && ".join([f"vault operator unseal {key}" for key in vault_keys.unseal_keys])
        ]

        try:
            await core_v1.connect_get_namespaced_pod_exec (
                pod_name,
                namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )

            return True
        except Exception:
            return False

async def vault_raft_join(namespace: str = "vault", pod_name: str = "vault-0") -> bool:
    """
    Join the Vault Raft cluster.
    This function is used to join the Vault pod to the Raft cluster.
    """
    async with kubernetes_asyncio.stream.WsApiClient() as api_client:
        core_v1 = kubernetes_asyncio.client.CoreV1Api(api_client=api_client)


        exec_command = [
            "/bin/sh",
            "-c",
            f"vault operator raft join -address=http://{pod_name}.vault-server-headless:8200   http://vault-0.vault-server-headless:8200"
        ]

        try:
            await core_v1.connect_get_namespaced_pod_exec (
                pod_name,
                namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )

            return True

        except Exception:
            return False

async def init_vault(namespace: str = "vault", pod_name: str = "vault-0") -> models.VaultKeys | None:
    """
    Initialize the vault for storing sensitive information.
    This function sets up the necessary configurations and checks
    if the vault is ready to use.
    """
    async with kubernetes_asyncio.stream.WsApiClient() as api_client:
        core_v1 = kubernetes_asyncio.client.CoreV1Api(api_client=api_client)

        exec_command = [
            "/bin/sh",
            "-c",
            "vault operator init -key-shares=5 -key-threshold=3"
        ]

        output = await core_v1.connect_get_namespaced_pod_exec (
            pod_name,
            namespace,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False
        )

        # Parse the output
        unseal_keys = re.findall(r"Unseal Key \d+: (.+)", output)
        root_token_match = re.search(r"Initial Root Token: (.+)", output)
        root_token = root_token_match.group(1) if root_token_match else None

        if len(unseal_keys) != 5 or not root_token:
            return None

        return models.VaultKeys(unseal_keys, root_token)

def enable_kv_v2_secrets_engine(root_token: str, url: str | None = None) -> bool:
    client = hvac.Client(url=url, token=root_token)
    try:
        client.sys.enable_secrets_engine (
            backend_type='kv',
            path='secret',
            options={'version': '2'}
        )
        return True
    except Exception:
        return False

def enable_kubernetes_authentication(root_token: str, url: str | None = None) -> bool:


    # Initialize Vault client
    client = hvac.Client(url=url, token=root_token)

    # Enable the Kubernetes auth method if not already enabled
    auths = client.sys.list_auth_methods()
    if "kubernetes/" not in auths:
        client.sys.enable_auth_method("kubernetes")

    # Configure the Vault Kubernetes auth method
    client.auth.kubernetes.configure(
        kubernetes_host="https://kubernetes.default.svc"
    )

    # Add the policy for the Kubernetes auth method
    client.sys.create_or_update_policy(
        name="external-secrets-policy",
        policy="""
        path "auth/kubernetes/login" {
            capabilities = ["create"]
        }

        path "*" {
            capabilities = ["read"]
        }
        """,
    )
    client.sys.create_or_update_policy(
        name="argocd-policy",
        policy="""
        path "auth/kubernetes/login" {
            capabilities = ["create"]
        }

        path "*" {
            capabilities = ["read"]
        }
        """,
    )
    # Create a role for the Kubernetes auth method
    client.adapter.request(
        method="POST",
        url="/v1/auth/kubernetes/role/external-secrets",
        json={
            "bound_service_account_names": ["external-secrets"],
            "bound_service_account_namespaces": ["external-secrets"],
            "policies": ["external-secrets-policy"],
            "alias_name_source": "serviceaccount_name",
            "ttl": "1h",
            "token_max_ttl": "2h",
            "audience": "k3s",
        },
    )

    client.adapter.request(
        method="POST",
        url="/v1/auth/kubernetes/role/argocd",
        json={
            "bound_service_account_names": ["argocd-argo-cd-argocd-repo-server"],
            "bound_service_account_namespaces": ["argocd"],
            "policies": ["argocd-policy"],
            "alias_name_source": "serviceaccount_name",
            "ttl": "1h",
            "token_max_ttl": "2h",
            "audience": "k3s",
        },
    )
    return True

@contextmanager
def port_forward_vault(namespace: str = "vault", pod_name: str = "vault-0"):
    """Forward the Vault port locally and yield the URL."""
    sock = socket.socket()
    sock.bind(("", 0))
    local_port = sock.getsockname()[1]
    sock.close()

    cmd = [
        "kubectl",
        "port-forward",
        f"pod/{pod_name}",
        f"{local_port}:8200",
        "-n",
        namespace,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    try:
        yield f"http://localhost:{local_port}"
    finally:
        proc.terminate()
        proc.wait()


def store_secrets(
    secrets: list[models.VaultSecret],
    root_token: str,
    url: str | None = None,
) -> bool:
    """Store the provided secrets in Vault."""

    client = hvac.Client(url=url, token=root_token)

    grouped: dict[str, dict[str, str]] = {}
    for secret in secrets:
        grouped.setdefault(secret.path, {})[secret.key] = secret.value.replace('\r', '')

    for path, data in grouped.items():
        try:
            client.secrets.kv.v2.create_or_update_secret(
                mount_point="secret",
                path=path,
                secret=data,
            )
        except Exception:
            return False
    return True


def read_secrets(
    root_token: str,
    url: str | None = None,
    namespace: str | None = None,
    name: str | None = None,
) -> list[models.VaultSecret]:
    """Read secrets from Vault.

    Args:
        root_token: Vault root token for authentication
        url: Vault URL (defaults to None, will use port-forward if needed)
        namespace: Optional namespace filter (e.g., "database-system")
        name: Optional secret name filter (e.g., "cluster-credentials")

    Returns:
        List of VaultSecret objects read from Vault
    """
    client = hvac.Client(url=url, token=root_token)
    secrets = []

    try:
        # List all secrets under system (path without leading slash for listing)
        list_response = client.secrets.kv.v2.list_secrets(
            mount_point="secret",
            path="system",
        )

        if not list_response or "data" not in list_response or "keys" not in list_response["data"]:
            return secrets

        # Iterate through namespaces
        for ns in list_response["data"]["keys"]:
            if namespace and ns != namespace:
                continue

            try:
                ns_list = client.secrets.kv.v2.list_secrets(
                    mount_point="secret",
                    path=f"system/{ns}",
                )

                if not ns_list or "data" not in ns_list or "keys" not in ns_list["data"]:
                    continue

                # Iterate through secret names in namespace
                for secret_name in ns_list["data"]["keys"]:
                    if name and secret_name != name:
                        continue

                    try:
                        # Read the secret (path without leading slash for read_secret_version)
                        secret_response = client.secrets.kv.v2.read_secret_version(
                            mount_point="secret",
                            path=f"system/{ns}/{secret_name}",
                        )

                        if secret_response and "data" in secret_response and "data" in secret_response["data"]:
                            secret_data = secret_response["data"]["data"]

                            # Create VaultSecret objects for each key-value pair
                            for key, value in secret_data.items():
                                secrets.append(
                                    models.VaultSecret(
                                        namespace=ns,
                                        name=secret_name,
                                        key=key,
                                        value=str(value),
                                        environment=None,  # Vault doesn't store environment info
                                    )
                                )
                    except Exception:
                        # Skip secrets that can't be read
                        continue
            except Exception:
                # Skip namespaces that can't be listed
                continue
    except Exception:
        # Return empty list if listing fails
        pass

    return secrets

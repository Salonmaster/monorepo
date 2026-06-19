from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import enums

if TYPE_CHECKING:
    from models import VaultKeys, Task, Credential
    from helpers.remote_db import SecretsDatabaseHandle
    from helpers.kubeconfig import RemoteKubeconfigHandle


class Context:
    environment: enums.Environment | None = None
    kubeconfig: str | None = None
    kubeconfig_handle: "RemoteKubeconfigHandle" | None = None
    secrets_db: str | None = None
    secrets_db_handle: "SecretsDatabaseHandle" | None = None
    vault_keys: VaultKeys | None = None
    secrets_db_password: str | None = None
    open_browser: bool = True
    program_start: datetime.date | None = None
    program_finished: datetime.date | None = None
    selected_task: Task | None = None
    credentials: list[Credential] | None = None
    selected_credential: Credential | None = None
    console_mode: bool = False
    vault_namespace: str = "vault"
    vault_pod_name: str = "vault-0"

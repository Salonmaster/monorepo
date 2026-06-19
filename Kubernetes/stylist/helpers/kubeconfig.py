from __future__ import annotations

import logging
import os
import shutil
import tempfile
from typing import Any, Callable, Tuple

from botocore.exceptions import ClientError

from .remote_db import (
    RemoteS3Config,
    create_s3_client,
    is_s3_path,
    normalize_s3_path,
    parse_s3_url,
)

LOG = logging.getLogger(__name__)


class RemoteKubeconfigHandle:
    """Download and manage kubeconfig files stored in S3-compatible storage."""

    def __init__(
        self,
        source_path: str,
        *,
        download: bool = True,
        auto_cleanup: bool = True,
        config: RemoteS3Config | None = None,
        client_factory: Callable[[RemoteS3Config | None], Any] = create_s3_client,
    ) -> None:
        if not is_s3_path(source_path):
            raise ValueError("RemoteKubeconfigHandle requires an s3:// path")
        self.source_path = normalize_s3_path(source_path)
        self.remote = parse_s3_url(self.source_path)
        self.config = config or RemoteS3Config.from_env()
        self._client_factory = client_factory
        self._client_instance = None
        self.auto_cleanup = auto_cleanup

        self._tmpdir = tempfile.mkdtemp(prefix="stylist-kubeconfig-")
        filename = os.path.basename(self.remote.key) or "kubeconfig"
        self.local_path = os.path.join(self._tmpdir, filename)

        if download:
            self._download_remote()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = self._client_factory(self.config)
        return self._client_instance

    def _download_remote(self) -> None:
        try:
            self._get_client().download_file(self.remote.bucket, self.remote.key, self.local_path)
            LOG.debug("Downloaded kubeconfig from %s", self.source_path)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(f"Remote kubeconfig {self.source_path} was not found") from exc
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self.auto_cleanup:
            self.cleanup()

    def cleanup(self) -> None:
        if self._tmpdir and os.path.isdir(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None


def prepare_kubeconfig(
    path: str | None,
    *,
    download: bool = True,
    auto_cleanup: bool = True,
) -> Tuple[str | None, RemoteKubeconfigHandle | None]:
    """Return a local path for kubeconfig files, downloading S3 objects when needed."""
    if not path:
        return None, None
    if not is_s3_path(path):
        return path, None
    normalized = normalize_s3_path(path)
    handle = RemoteKubeconfigHandle(
        normalized,
        download=download,
        auto_cleanup=auto_cleanup,
        client_factory=create_s3_client,
    )
    return handle.local_path, handle

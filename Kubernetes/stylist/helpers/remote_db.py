from __future__ import annotations
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, Callable, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteObject:
    bucket: str
    key: str


@dataclass
class RemoteS3Config:
    endpoint_url: str | None = None
    region: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    session_token: str | None = None

    @classmethod
    def from_env(cls) -> "RemoteS3Config":
        return cls(
            endpoint_url=os.getenv("AWS_S3_ENDPOINT") or os.getenv("AWS_ENDPOINT_URL"),
            region=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            session_token=os.getenv("AWS_SESSION_TOKEN"),
        )


def normalize_s3_path(path: str) -> str:
    """Normalize user input into a canonical s3://bucket/key URL."""
    if path.lower().startswith("s3://"):
        scheme, rest = path[:5], path[5:]
        rest = rest.lstrip("/\\")
        rest = rest.replace("\\", "/")
        return scheme + rest
    if path.lower().startswith("s3:"):
        rest = path[3:]
        rest = rest.lstrip("/\\")
        rest = rest.replace("\\", "/")
        return f"s3://{rest}"
    return path


def is_s3_path(path: str | None) -> bool:
    if not path:
        return False
    return path.lower().startswith("s3:")


def parse_s3_url(url: str) -> RemoteObject:
    parsed = urlparse(url)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"Invalid S3 URL: {url}")
    key = parsed.path.lstrip("/")
    if not key:
        raise ValueError("S3 URL must include an object key")
    return RemoteObject(bucket=parsed.netloc, key=key)


def create_s3_client(config: RemoteS3Config | None = None):
    cfg = config or RemoteS3Config.from_env()
    session = boto3.session.Session(
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        aws_session_token=cfg.session_token,
        region_name=cfg.region or "us-east-1",
    )
    return session.client("s3", endpoint_url=cfg.endpoint_url)


class SecretsDatabaseHandle:
    """Manage downloading and uploading the secrets DB from S3-compatible storage."""

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
            raise ValueError("SecretsDatabaseHandle requires an s3:// path")
        self.source_path = source_path
        self.remote = parse_s3_url(source_path)
        self.config = config or RemoteS3Config.from_env()
        self._client_factory = client_factory
        self._client_instance = None
        self._dirty = False
        self._tmpdir = tempfile.mkdtemp(prefix="stylist-secrets-db-")
        os.makedirs(self._tmpdir, exist_ok=True)
        filename = os.path.basename(self.remote.key) or "secrets.db"
        self.local_path = os.path.join(self._tmpdir, filename)
        if download:
            self._download_remote()
        self.auto_cleanup = auto_cleanup

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client_instance is None:
            self._client_instance = self._client_factory(self.config)
        return self._client_instance

    def _download_remote(self) -> None:
        try:
            self._get_client().download_file(self.remote.bucket, self.remote.key, self.local_path)
            LOG.debug("Downloaded secrets DB from %s", self.source_path)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey"}:
                LOG.info("Remote secrets DB %s not found; a new file will be created when saved.", self.source_path)
            else:
                raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mark_dirty(self) -> None:
        self._dirty = True

    def sync(self, *, force: bool = False) -> None:
        if not (force or self._dirty):
            return
        self._get_client().upload_file(self.local_path, self.remote.bucket, self.remote.key)
        self._dirty = False
        LOG.debug("Uploaded secrets DB to %s", self.source_path)

    def close(self) -> None:
        try:
            self.sync()
        finally:
            if self.auto_cleanup:
                self.cleanup()

    def cleanup(self) -> None:
        if self._tmpdir and os.path.isdir(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None


def prepare_secrets_db(
    path: str | None,
    *,
    download: bool = True,
    auto_cleanup: bool = True,
) -> Tuple[str | None, SecretsDatabaseHandle | None]:
    if not path:
        return None, None
    if not is_s3_path(path):
        return path, None
    normalized = normalize_s3_path(path)
    handle = SecretsDatabaseHandle(
        normalized,
        download=download,
        auto_cleanup=auto_cleanup,
        client_factory=create_s3_client,
    )
    return handle.local_path, handle

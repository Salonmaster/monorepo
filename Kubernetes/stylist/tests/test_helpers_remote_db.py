import sys
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.helpers import remote_db  # noqa: E402


def test_normalize_and_detect_s3_paths():
    assert remote_db.normalize_s3_path("s3://bucket/key") == "s3://bucket/key"
    assert remote_db.normalize_s3_path("s3:/bucket/key") == "s3://bucket/key"
    assert remote_db.normalize_s3_path("s3:\\bucket\\key") == "s3://bucket/key"
    assert remote_db.normalize_s3_path("local/path") == "local/path"

    assert remote_db.is_s3_path("s3://bucket/key") is True
    assert remote_db.is_s3_path("S3://bucket/key") is True
    assert remote_db.is_s3_path("/tmp/file") is False
    assert remote_db.is_s3_path(None) is False


def test_parse_s3_url_validation():
    obj = remote_db.parse_s3_url("s3://bucket-name/path/to/file")
    assert obj.bucket == "bucket-name"
    assert obj.key == "path/to/file"

    with pytest.raises(ValueError):
        remote_db.parse_s3_url("https://bucket/key")
    with pytest.raises(ValueError):
        remote_db.parse_s3_url("s3://bucket")


class DummyClient:
    def __init__(self, initial_contents: str = "existing"):
        self.download_calls = []
        self.upload_calls = []
        self._initial_contents = initial_contents
        self.uploaded_payloads = []

    def download_file(self, bucket, key, destination):
        self.download_calls.append((bucket, key, destination))
        Path(destination).write_text(self._initial_contents)

    def upload_file(self, source, bucket, key):
        self.upload_calls.append((source, bucket, key))
        self.uploaded_payloads.append(Path(source).read_text())


def test_secrets_handle_downloads_and_syncs(tmp_path):
    client = DummyClient(initial_contents="initial")
    config = remote_db.RemoteS3Config(region="us-east-1")

    handle = remote_db.SecretsDatabaseHandle(
        "s3://my-bucket/secrets.db",
        config=config,
        client_factory=lambda _cfg: client,
    )

    # Download should have populated the local file
    assert Path(handle.local_path).read_text() == "initial"

    Path(handle.local_path).write_text("updated")
    handle.mark_dirty()
    handle.sync()

    assert client.upload_calls
    assert client.uploaded_payloads[-1] == "updated"

    handle.close()
    assert handle._tmpdir is None


def test_handle_allows_missing_remote_object():
    class MissingClient(DummyClient):
        def download_file(self, bucket, key, destination):  # noqa: ARG002
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "download_file")

    client = MissingClient()
    config = remote_db.RemoteS3Config(region="us-east-1")

    handle = remote_db.SecretsDatabaseHandle(
        "s3://bucket/does-not-exist.db",
        config=config,
        client_factory=lambda _cfg: client,
    )
    # Creation should succeed even if the remote object is missing
    assert Path(handle.local_path).name == "does-not-exist.db"
    assert Path(handle.local_path).parent.exists()
    handle.close()


def test_prepare_secrets_db_returns_handle_for_s3(tmp_path, monkeypatch):
    client = DummyClient()
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setattr(remote_db, "create_s3_client", lambda config: client)

    handle_path, handle = remote_db.prepare_secrets_db(
        "s3://bucket/example.db",
        download=True,
        auto_cleanup=False,
    )
    assert handle is not None
    assert handle_path == handle.local_path
    handle.cleanup()

    local_path, local_handle = remote_db.prepare_secrets_db(str(tmp_path / "local.db"))
    assert local_path == str(tmp_path / "local.db")
    assert local_handle is None

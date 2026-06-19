from pathlib import Path

import pytest
from botocore.exceptions import ClientError

import stylist.helpers.remote_db as remote_db

class FakeStorage:
    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}


class FakeS3Client:
    def __init__(self, storage: FakeStorage, should_exist: bool = True):
        self.storage = storage
        self.should_exist = should_exist

    def download_file(self, bucket: str, key: str, dest: str) -> None:
        obj_key = (bucket, key)
        if obj_key not in self.storage.objects:
            error_response = {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}
            raise ClientError(error_response, "GetObject")
        Path(dest).write_bytes(self.storage.objects[obj_key])

    def upload_file(self, src: str, bucket: str, key: str) -> None:
        self.storage.objects[(bucket, key)] = Path(src).read_bytes()


@pytest.fixture
def storage():
    return FakeStorage()


def test_prepare_returns_local_path_for_files(tmp_path):
    local_file = tmp_path / "secrets.db"
    local_file.write_text("hello")
    resolved, handle = remote_db.prepare_secrets_db(str(local_file))
    assert resolved == str(local_file)
    assert handle is None


def test_downloads_existing_remote_file(tmp_path, storage):
    storage.objects[("bucket", "path/to/db")] = b"remote-data"

    def factory(_config):
        return FakeS3Client(storage)

    handle = remote_db.SecretsDatabaseHandle(
        "s3://bucket/path/to/db",
        client_factory=factory,
        auto_cleanup=False,
    )
    assert Path(handle.local_path).read_bytes() == b"remote-data"
    handle.cleanup()


def test_uploads_when_dirty(storage):
    def factory(_config):
        return FakeS3Client(storage)

    handle = remote_db.SecretsDatabaseHandle(
        "s3://bucket/path/to/db",
        client_factory=factory,
        auto_cleanup=False,
    )
    Path(handle.local_path).write_text("new")
    handle.mark_dirty()
    handle.sync()
    assert storage.objects[("bucket", "path/to/db")] == b"new"
    handle.cleanup()


def test_prepare_secrets_db_with_remote_path(storage, monkeypatch):
    storage.objects[("bucket", "remote/secret.db")] = b"abc"

    def factory(_config):
        return FakeS3Client(storage)

    monkeypatch.setattr(remote_db, "create_s3_client", lambda config: factory(config))

    path, handle = remote_db.prepare_secrets_db(
        "s3://bucket/remote/secret.db",
        download=True,
        auto_cleanup=False,
    )
    assert handle is not None
    assert Path(path).read_bytes() == b"abc"
    handle.cleanup()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("s3://bucket/path/file.db", "s3://bucket/path/file.db"),
        ("s3:/bucket/path/file.db", "s3://bucket/path/file.db"),
        ("s3:\\bucket\\path\\file.db", "s3://bucket/path/file.db"),
        ("s3:bucket/path/file.db", "s3://bucket/path/file.db"),
    ],
)
def test_normalize_s3_path(raw, expected):
    assert remote_db.normalize_s3_path(raw) == expected

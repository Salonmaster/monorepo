import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.helpers import kubeconfig as kubeconfig_helper  # noqa: E402


class FakeS3Client:
    def __init__(self, storage: dict[tuple[str, str], str]):
        self.storage = storage

    def download_file(self, bucket: str, key: str, destination: str) -> None:
        payload = self.storage.get((bucket, key))
        if payload is None:
            from botocore.exceptions import ClientError

            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        Path(destination).write_text(payload)


def test_prepare_kubeconfig_returns_local_path(tmp_path):
    kubeconfig = tmp_path / "config"
    kubeconfig.write_text("local")

    resolved, handle = kubeconfig_helper.prepare_kubeconfig(str(kubeconfig))
    assert resolved == str(kubeconfig)
    assert handle is None


def test_prepare_kubeconfig_downloads_remote(monkeypatch):
    storage = {("bucket", "clusters/tst/kubeconfig"): "apiVersion: v1"}

    def factory(_config):
        return FakeS3Client(storage)

    monkeypatch.setattr(kubeconfig_helper, "create_s3_client", lambda config: factory(config))

    path, handle = kubeconfig_helper.prepare_kubeconfig(
        "s3://bucket/clusters/tst/kubeconfig",
        download=True,
        auto_cleanup=False,
    )
    assert handle is not None
    assert Path(path).read_text() == "apiVersion: v1"
    handle.cleanup()


def test_missing_remote_kubeconfig_raises(monkeypatch):
    storage = {}

    def factory(_config):
        return FakeS3Client(storage)

    monkeypatch.setattr(kubeconfig_helper, "create_s3_client", lambda config: factory(config))

    with pytest.raises(FileNotFoundError):
        kubeconfig_helper.prepare_kubeconfig("s3://bucket/missing.cfg")

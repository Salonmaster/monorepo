import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stylist.helpers import helm  # noqa: E402


class DummyProcess:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self):
        return self._stdout, self._stderr


def _install_fake_subprocess(monkeypatch, process):
    async def fake_create(*args, **kwargs):  # noqa: ANN001
        fake_create.captured_args = args
        fake_create.captured_kwargs = kwargs
        return process

    fake_create.captured_args = None
    fake_create.captured_kwargs = None
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    return fake_create


def test_exec_helm_command_uses_devnull(monkeypatch):
    process = DummyProcess(returncode=0, stdout=b"ok", stderr=b"")
    fake_create = _install_fake_subprocess(monkeypatch, process)

    code, stdout, stderr = asyncio.run(helm._exec_helm_command(["helm", "version"]))  # type: ignore[attr-defined]

    assert code == 0
    assert stdout == b"ok"
    assert fake_create.captured_kwargs["stdin"] is asyncio.subprocess.DEVNULL
    assert fake_create.captured_kwargs["stdout"] is asyncio.subprocess.PIPE
    assert fake_create.captured_kwargs["stderr"] is asyncio.subprocess.PIPE


def test_install_chart_includes_values_file(monkeypatch):
    recorded = {}

    async def fake_exec(command):  # noqa: ANN001
        recorded["command"] = command
        return 0, b"", b""

    monkeypatch.setattr(helm, "_exec_helm_command", fake_exec)

    success = asyncio.run(helm.install_chart("./charts/app", "release", namespace="ns", values_file="values.yaml"))

    assert success is True
    assert recorded["command"] == [
        "helm",
        "install",
        "release",
        os.path.normpath("./charts/app"),
        "--namespace",
        "ns",
        "--create-namespace",
        "-f",
        os.path.normpath("values.yaml"),
    ]


def test_install_chart_failure_logs(monkeypatch):
    logged = {}

    async def fake_exec(command):  # noqa: ANN001
        logged["command"] = command
        return 1, b"", b"boom"

    def fake_log(command, stdout, stderr):  # noqa: ANN001
        logged["failure"] = (command, stdout, stderr)

    monkeypatch.setattr(helm, "_exec_helm_command", fake_exec)
    monkeypatch.setattr(helm, "_log_helm_failure", fake_log)

    success = asyncio.run(helm.install_chart("chart", "release"))

    assert success is False
    assert logged["failure"][0][0] == "helm"


def test_check_helm_availability_returns_false_on_spawn_failure(monkeypatch):
    async def fake_exec(command):  # noqa: ANN001
        return None, b"", b""

    monkeypatch.setattr(helm, "_exec_helm_command", fake_exec)

    assert asyncio.run(helm.check_helm_availability()) is False

import os
import models
import subprocess
import json
import asyncio
import typer
from typing import Sequence


def _decode_stream(data: bytes | None) -> str:
    if not data:
        return ""
    return data.decode("utf-8", errors="replace").strip()


def _log_helm_failure(command: Sequence[str], stdout: bytes | None, stderr: bytes | None) -> None:
    cmd_str = " ".join(command)
    typer.secho(f"Helm command failed: {cmd_str}", fg=typer.colors.RED)
    decoded_stdout = _decode_stream(stdout)
    decoded_stderr = _decode_stream(stderr)
    if decoded_stdout:
        typer.secho("stdout:", fg=typer.colors.YELLOW)
        typer.echo(decoded_stdout)
    if decoded_stderr:
        typer.secho("stderr:", fg=typer.colors.YELLOW)
        typer.echo(decoded_stderr)


def _log_spawn_exception(command: Sequence[str], exc: Exception) -> None:
    cmd_str = " ".join(command)
    typer.secho(f"Failed to execute Helm command: {cmd_str}", fg=typer.colors.RED)
    typer.secho(f"Reason: {exc}", fg=typer.colors.RED)


async def _exec_helm_command(command: Sequence[str]) -> tuple[int | None, bytes, bytes]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
    except Exception as exc:
        _log_spawn_exception(command, exc)
        return None, b"", b""

    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr

async def check_helm_availability() -> bool:
    """
    Check if Helm is installed and available in the system PATH.
    """
    command = ["helm", "version", "--short"]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return False
    if returncode == 0:
        return True
    _log_helm_failure(command, stdout, stderr)
    return False

async def get_configured_repositories() -> list[models.HelmRepository]:
    command = ["helm", "repo", "list", "-o", "json"]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return []
    if returncode != 0:
        _log_helm_failure(command, stdout, stderr)
        return []
    repos = json.loads(stdout.decode())
    return [models.HelmRepository(name=repo["name"], url=repo["url"]) for repo in repos]

async def add_helm_repo(repository: models.HelmRepository) -> bool:
    """
    Add a Helm repository. If the repo already exists, delete it first.

    Args:
        repo_name (str): The name of the Helm repository.
        repo_url (str): The URL of the Helm repository.
    """
    command = ["helm", "repo", "add", repository.name, repository.url]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return False
    if returncode != 0:
        _log_helm_failure(command, stdout, stderr)
        return False
    return True

async def dependency_build(chart_path: str) -> bool:
    """
    Build dependencies for the Helm chart.
    """
    command = ["helm", "dependency", "build", chart_path]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return False
    if returncode == 0:
        return True
    _log_helm_failure(command, stdout, stderr)
    return False

async def install_chart(chart_path: str, release_name: str, namespace: str = "default", values_file: str | None = None) -> bool:
    """
    Install a Helm chart.
    """

    normalized_chart_path = os.path.normpath(chart_path)
    normalized_values_file = os.path.normpath(values_file) if values_file else None
    command = [
        "helm", "install", release_name, normalized_chart_path,
        "--namespace", namespace, "--create-namespace",
    ]
    if normalized_values_file:
        command += ["-f", normalized_values_file]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return False
    if returncode == 0:
        return True
    _log_helm_failure(command, stdout, stderr)
    return False


async def uninstall_chart(release_name: str, namespace: str = "default") -> bool:
    """
    Uninstall a Helm release.
    """
    command = ["helm", "uninstall", release_name, "--namespace", namespace]
    returncode, stdout, stderr = await _exec_helm_command(command)
    if returncode is None:
        return False
    if returncode == 0:
        return True
    _log_helm_failure(command, stdout, stderr)
    return False

async def check_chart_installed(release_name: str, namespace: str = "default") -> bool:
    """
    Check if a Helm release is installed.

    Args:
        release_name (str): The name of the Helm release.
        namespace (str): The namespace where the release is installed.

    Returns:
        bool: True if the release is installed, False otherwise.
    """
    try:
        await asyncio.create_subprocess_exec(
            "helm", "status", release_name, "--namespace", namespace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError:
        return False

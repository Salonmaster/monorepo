import asyncio
import typer

from stylist import helpers


def show_environment() -> None:
    """Print the current cluster environment value if it exists."""
    env_value = asyncio.run(helpers.cluster.fetch_cluster_environment())
    typer.echo(env_value.value if env_value else "")

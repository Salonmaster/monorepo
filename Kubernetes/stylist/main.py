import datetime
import core
import typer

# Dynamically import all command modules to register them with the Typer app
import importlib
importlib.import_module("commands")

@core.Backbone().typer_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Stylist CLI for managing Kubernetes-based Salonmaster deployments."""
    core.Backbone().context.program_start = datetime.datetime.now()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)

def run_stylist():

    core.Backbone().typer_app()

if __name__ == "__main__":
    # Load command modules before running the app
    run_stylist()

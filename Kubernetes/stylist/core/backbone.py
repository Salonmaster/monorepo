from dotenv import load_dotenv
import typer
import datetime
from .context import Context

load_dotenv()

class Backbone:
    context = None
    _instance = None
    typer_app = None
    time_started = None


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Backbone, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Initialize your singleton attributes here
        if self.typer_app is None:
            self.typer_app = typer.Typer()
        if self.context is None:
            self.context = Context()
        if self.time_started is None:
            self.time_started = datetime.datetime.now()

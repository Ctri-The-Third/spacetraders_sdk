"""Wrapper for the Space Traders API."""

# create a "resources" folder if it doesn't already exist in the installed directory
import os
from pathlib import Path

dir_path = os.path.dirname(os.path.realpath(__file__))
Path(f"{dir_path}/resources").mkdir(parents=True, exist_ok=True)

from .client_mediator import SpaceTradersMediatorClient as SpaceTraders
from . import pg_pieces

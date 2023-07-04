# Copyright Modal Labs 2022
from contextlib import contextmanager
from datetime import datetime
from typing import Union, List

import click
from grpclib import GRPCError, Status

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.json import JSON

from modal.exception import NotFoundError


def timestamp_to_local(ts: float) -> str:
    if ts > 0:
        locale_tz = datetime.now().astimezone().tzinfo
        dt = datetime.fromtimestamp(ts, tz=locale_tz)
        return dt.isoformat(sep=" ", timespec="seconds")
    else:
        return None


def _plain(text: Union[Text, str]) -> str:
    return text.plain if isinstance(text, Text) else text


def display_table(column_names: List[str], rows: List[List[Union[Text, str]]], json: bool, title: str = None):
    console = Console()
    if json:
        json_data = [{col: _plain(row[i]) for i, col in enumerate(column_names)} for row in rows]
        console.print(JSON.from_data(json_data))
    else:
        table = Table(*column_names, title=title)
        for row in rows:
            table.add_row(*row)
        console.print(table)


def display_selection(choices: List[str], active: str, json: bool):
    console = Console()
    if json:
        json_data = [{"name": choice, "active": choice == active} for choice in choices]
        console.print(JSON.from_data(json_data))
    else:
        for choice in choices:
            text = Text(f"{choice} [active]", style="green") if active == choice else Text(choice, style="dim")
            console.print(text)


ENV_OPTION_HELP = """Environment to interact with

If none is specified, Modal will use the default environment of your current profile (can also be specified via the environment variable MODAL_ENVIRONMENT).
If neither is set, Modal will assume there is only one environment in the active workspace and use that one, or raise an error if there are multiple environments.
"""
ENV_OPTION = typer.Option(default=None, help=ENV_OPTION_HELP)


@contextmanager
def cli_grpc_errors():
    try:
        yield
    except GRPCError as exc:
        if exc.status == Status.INVALID_ARGUMENT:
            # makes longer/formatted errors easier to read
            raise click.UsageError(exc.message)
        elif exc.status == Status.NOT_FOUND:
            raise click.ClickException(f"Not found: {exc.message}")
        raise
    except NotFoundError as exc:
        raise click.ClickException(f"Not found: {str(exc)}")

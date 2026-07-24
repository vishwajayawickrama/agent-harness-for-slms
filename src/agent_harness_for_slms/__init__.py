from importlib.metadata import version

import typer
from rich.console import Console

app = typer.Typer(
    help="A CLI agent harness for small language models.",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version_flag: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the installed package version.",
        is_eager=True,
    ),
) -> None:
    if version_flag:
        console.print(version("agent-harness-for-slms"))
        raise typer.Exit

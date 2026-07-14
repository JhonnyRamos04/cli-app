"""Typer CLI surface for cli-app.

PR 1 ships the ``split`` and ``reconcile`` commands as documented stubs so
that ``cli-app --help`` already exposes the full command list. The full
implementations land in PR 2 (``split``) and PR 3 (``reconcile``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

app: typer.Typer = typer.Typer(
    name="cli-app",
    help="Split monolithic Python files into packages and reconcile their imports.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def split(
    source: Annotated[Path, typer.Argument(help="Path to the monolithic .py file.")],
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip the confirmation prompt and apply the split immediately.",
        ),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            help="Directory for the new package (default: adjacent to the source file).",
        ),
    ] = None,
) -> None:
    """Split a monolithic Python file into a structured package."""
    raise NotImplementedError("split lands in PR 2")


@app.command()
def reconcile(
    package_dir: Annotated[Path, typer.Argument(help="Path to the split package directory.")],
    project: Annotated[
        Path | None,
        typer.Option(
            "--project",
            help="Path to the project root for the global import rewrite pass.",
        ),
    ] = None,
) -> None:
    """Rewrite intra-package imports; optionally rewrite imports across a project."""
    raise NotImplementedError("reconcile lands in PR 3")

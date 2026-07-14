"""AST-based source parser.

The parser is intentionally minimal: it reads the file with ``encoding='utf-8'``
and hands the source to :func:`ast.parse` with ``type_comments=True`` so that
``ast.get_source_segment`` can recover the verbatim text of every node in a
later stage.
"""

from __future__ import annotations

import ast
from pathlib import Path


def parse_source(path: Path) -> ast.Module:
    """Read a Python source file and return its parsed AST module.

    Args:
        path: The path to the Python source file.

    Returns:
        The parsed :class:`ast.Module`.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        SyntaxError: If the source contains invalid Python syntax.
        UnicodeDecodeError: If the source is not valid UTF-8.
    """
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path), type_comments=True)

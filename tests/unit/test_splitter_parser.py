"""Unit tests for :mod:`cli_app.splitter.parser`."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cli_app.splitter.parser import parse_source


def test_parse_source_returns_ast_module(tmp_path: Path) -> None:
    """parse_source returns an ``ast.Module`` for a valid file."""
    source_file = tmp_path / "hello.py"
    source_file.write_text("x = 1\n", encoding="utf-8")

    tree = parse_source(source_file)

    assert isinstance(tree, ast.Module)
    assert len(tree.body) == 1


def test_parse_source_reads_with_utf8(tmp_path: Path) -> None:
    """parse_source decodes non-ASCII source as UTF-8."""
    source_file = tmp_path / "unicode.py"
    source_file.write_text('GREETING = "héllo wörld — ünïcödé"\n', encoding="utf-8")

    tree = parse_source(source_file)

    assert isinstance(tree.body[0], ast.Assign)
    constant_node = tree.body[0].value
    assert isinstance(constant_node, ast.Constant)
    assert isinstance(constant_node.value, str)
    assert "héllo" in constant_node.value


def test_parse_source_handles_decorated_class(tmp_path: Path) -> None:
    """parse_source preserves decorator lists on top-level ClassDef."""
    source_file = tmp_path / "decorated.py"
    source_file.write_text(
        "@dataclass\nclass Foo:\n    x: int = 0\n",
        encoding="utf-8",
    )

    tree = parse_source(source_file)

    class_node = tree.body[0]
    assert isinstance(class_node, ast.ClassDef)
    assert class_node.name == "Foo"
    assert len(class_node.decorator_list) == 1


def test_parse_source_raises_for_missing_file(tmp_path: Path) -> None:
    """parse_source raises FileNotFoundError when the path does not exist."""
    with pytest.raises(FileNotFoundError):
        parse_source(tmp_path / "does_not_exist.py")


def test_parse_source_raises_for_syntax_error(tmp_path: Path) -> None:
    """parse_source raises SyntaxError when the source is invalid Python."""
    source_file = tmp_path / "bad.py"
    source_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    with pytest.raises(SyntaxError):
        parse_source(source_file)

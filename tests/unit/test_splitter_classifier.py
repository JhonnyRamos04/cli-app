"""Unit tests for :mod:`cli_app.splitter.classifier`."""

from __future__ import annotations

import ast
from pathlib import Path

from cli_app.splitter.classifier import (
    Definition,
    DefinitionKind,
    classify_node,
    classify_top_level,
)


def _tree(source: str) -> tuple[ast.Module, str]:
    """Parse an inline source string into (tree, source) for convenience."""
    return ast.parse(source), source


def test_classify_node_maps_classdef_to_class() -> None:
    """classify_node returns CLASS for a plain ClassDef."""
    tree, text = _tree("class A:\n    pass\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "A"
    assert result.kind is DefinitionKind.CLASS
    assert result.lineno == 1
    assert "class A" in result.source_segment


def test_classify_node_maps_functiondef_to_function() -> None:
    """classify_node returns FUNCTION for FunctionDef."""
    tree, text = _tree("def f():\n    return 1\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "f"
    assert result.kind is DefinitionKind.FUNCTION


def test_classify_node_maps_async_functiondef_to_function() -> None:
    """classify_node returns FUNCTION for AsyncFunctionDef (REQ-ABD-001)."""
    tree, text = _tree("async def f():\n    return 1\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "f"
    assert result.kind is DefinitionKind.FUNCTION


def test_classify_node_keeps_decorated_class_as_class() -> None:
    """Decorated ClassDef is still classified as CLASS (REQ-ABD-001)."""
    tree, text = _tree("@dataclass\nclass A:\n    x: int = 0\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "A"
    assert result.kind is DefinitionKind.CLASS


def test_classify_node_keeps_decorated_function_as_function() -> None:
    """Decorated FunctionDef is still classified as FUNCTION (REQ-ABD-001)."""
    tree, text = _tree("@staticmethod\ndef f() -> int:\n    return 1\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "f"
    assert result.kind is DefinitionKind.FUNCTION


def test_classify_node_uppercase_assign_is_constant() -> None:
    """Uppercase Name target in Assign maps to CONSTANT."""
    tree, text = _tree("MAX_SIZE = 100\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "MAX_SIZE"
    assert result.kind is DefinitionKind.CONSTANT


def test_classify_node_lowercase_assign_is_unclassified() -> None:
    """Lowercase Name target in Assign maps to UNCLASSIFIED (not a constant)."""
    tree, text = _tree("counter = 0\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "counter"
    assert result.kind is DefinitionKind.UNCLASSIFIED


def test_classify_node_import_is_import_block() -> None:
    """A bare ``import`` statement maps to IMPORT_BLOCK."""
    tree, text = _tree("import os\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "imports"
    assert result.kind is DefinitionKind.IMPORT_BLOCK


def test_classify_node_importfrom_is_import_block() -> None:
    """A ``from ... import ...`` statement maps to IMPORT_BLOCK."""
    tree, text = _tree("from pathlib import Path\n")

    result = classify_node(tree.body[0], text)

    assert result.name == "imports"
    assert result.kind is DefinitionKind.IMPORT_BLOCK


def test_classify_node_top_level_expr_is_unclassified() -> None:
    """A top-level expression statement maps to UNCLASSIFIED (REQ-ABD-002)."""
    tree, text = _tree('print("hello")\n')

    result = classify_node(tree.body[0], text)

    assert result.kind is DefinitionKind.UNCLASSIFIED
    assert result.lineno == 1


def test_classify_top_level_groups_by_kind_in_source_order() -> None:
    """classify_top_level groups by kind and preserves source order
    within each group (REQ-ABD-001)."""
    tree, text = _tree(
        "class A:\n    pass\ndef f():\n    return 1\nclass B:\n    pass\ndef g():\n    return 2\n"
    )

    result = classify_top_level(tree, text)

    by_kind: dict[DefinitionKind, list[Definition]] = {}
    for definition in result:
        by_kind.setdefault(definition.kind, []).append(definition)

    assert [d.name for d in by_kind[DefinitionKind.CLASS]] == ["A", "B"]
    assert [d.name for d in by_kind[DefinitionKind.FUNCTION]] == ["f", "g"]


def test_classify_top_level_merges_all_imports_into_one_block() -> None:
    """All import statements in the module collapse to a single
    IMPORT_BLOCK regardless of position in the source."""
    tree, text = _tree("import os\nMAX = 100\nimport sys\nfrom pathlib import Path\n")

    result = classify_top_level(tree, text)

    import_blocks = [d for d in result if d.kind is DefinitionKind.IMPORT_BLOCK]
    assert len(import_blocks) == 1
    assert "import os" in import_blocks[0].source_segment
    assert "import sys" in import_blocks[0].source_segment
    assert "from pathlib import Path" in import_blocks[0].source_segment


def test_classify_top_level_class_inside_if_is_unclassified() -> None:
    """ClassDef inside an ``if`` block is UNCLASSIFIED (REQ-ABD-002)."""
    tree, text = _tree(
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    class _Helper:\n        pass\n"
    )

    result = classify_top_level(tree, text)

    unclassified = [d for d in result if d.kind is DefinitionKind.UNCLASSIFIED]
    unclassified_names = {d.name for d in unclassified}
    assert "_Helper" in unclassified_names


def test_classify_top_level_function_inside_try_is_unclassified() -> None:
    """FunctionDef inside a ``try`` block is UNCLASSIFIED."""
    tree, text = _tree("try:\n    def _helper():\n        return 1\nexcept Exception:\n    pass\n")

    result = classify_top_level(tree, text)

    unclassified = [d for d in result if d.kind is DefinitionKind.UNCLASSIFIED]
    unclassified_names = {d.name for d in unclassified}
    assert "_helper" in unclassified_names


def test_classify_top_level_returns_empty_tuple_for_empty_module(
    tmp_path: Path,
) -> None:
    """An empty module yields no definitions."""
    tree, text = _tree("")

    result = classify_top_level(tree, text)

    assert result == ()

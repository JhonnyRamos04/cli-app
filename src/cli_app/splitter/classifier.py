"""Top-level definition classification.

Maps raw :mod:`ast` nodes to :class:`Definition` records. Decorated
``ClassDef`` / ``FunctionDef`` keep their kind (REQ-ABD-001). Statements
that do not match a known category — ``If`` / ``Try`` / ``Expr`` / ``AnnAssign``
/ augmented ``Assign`` and any other top-level node — land in the
``unclassified`` bucket (REQ-ABD-002). Assignments whose target is an
uppercase ``Name`` are treated as module-level constants.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum


class DefinitionKind(StrEnum):
    """The kind of a top-level definition in a Python module."""

    CLASS = "class"
    FUNCTION = "function"
    CONSTANT = "constant"
    IMPORT_BLOCK = "import_block"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True, slots=True)
class Definition:
    """A single top-level definition extracted from a Python source file.

    Attributes:
        name: A stable identifier for the definition. For classes, functions,
            and async functions this is the symbol name. For assignment
            constants it is the (uppercase) target name. For an import block
            it is the literal string ``"imports"``. For unclassified items it
            is a synthetic name of the form ``unclassified_at_line_<N>``.
        kind: The classification bucket.
        lineno: The 1-based line number where the definition starts.
        end_lineno: The 1-based line number where the definition ends.
        source_segment: The verbatim source text spanning the definition.
    """

    name: str
    kind: DefinitionKind
    lineno: int
    end_lineno: int
    source_segment: str


def _segment(source: str, node: ast.stmt) -> str:
    """Return the verbatim source segment for ``node``.

    Falls back to :func:`ast.unparse` when :func:`ast.get_source_segment`
    cannot extract a segment (defensive — should not happen for top-level
    nodes that parsed cleanly).
    """
    segment = ast.get_source_segment(source, node)
    if segment is None:
        return ast.unparse(node)
    return segment


def _name_of_assign(node: ast.Assign) -> str:
    """Extract a stable name from a single-target ``ast.Assign``.

    Falls back to ``assign_at_line_<N>`` for tuple / attribute / subscript
    targets where no single name is meaningful.
    """
    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return f"assign_at_line_{node.lineno}"


def _is_constant_name(name: str) -> bool:
    """Heuristic for ``UPPER_CASE`` module-level constants.

    Returns ``True`` only for non-empty names that are all uppercase and
    contain at least one alphabetic character. This matches the Python
    convention for module-level constants and avoids treating ``x = 1`` as
    one.
    """
    if not name:
        return False
    if name.upper() != name:
        return False
    return any(char.isalpha() for char in name)


def classify_node(node: ast.stmt, source: str) -> Definition:
    """Classify a single top-level statement.

    Args:
        node: A top-level AST statement.
        source: The full source text (used to extract the source segment).

    Returns:
        A :class:`Definition` for the node. Statements that do not match
        a known category (including ``If``, ``Try``, ``Expr``, ``AnnAssign``
        and augmented ``Assign``) return ``kind=UNCLASSIFIED``.
    """
    end_lineno = node.end_lineno if node.end_lineno is not None else node.lineno
    if isinstance(node, ast.ClassDef):
        return Definition(
            name=node.name,
            kind=DefinitionKind.CLASS,
            lineno=node.lineno,
            end_lineno=end_lineno,
            source_segment=_segment(source, node),
        )
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return Definition(
            name=node.name,
            kind=DefinitionKind.FUNCTION,
            lineno=node.lineno,
            end_lineno=end_lineno,
            source_segment=_segment(source, node),
        )
    if isinstance(node, ast.Assign):
        name = _name_of_assign(node)
        kind = DefinitionKind.CONSTANT if _is_constant_name(name) else DefinitionKind.UNCLASSIFIED
        return Definition(
            name=name,
            kind=kind,
            lineno=node.lineno,
            end_lineno=end_lineno,
            source_segment=_segment(source, node),
        )
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return Definition(
            name="imports",
            kind=DefinitionKind.IMPORT_BLOCK,
            lineno=node.lineno,
            end_lineno=end_lineno,
            source_segment=_segment(source, node),
        )
    return Definition(
        name=f"unclassified_at_line_{node.lineno}",
        kind=DefinitionKind.UNCLASSIFIED,
        lineno=node.lineno,
        end_lineno=end_lineno,
        source_segment=_segment(source, node),
    )


def _harvest_inner_unclassified(nodes: list[ast.stmt], source: str) -> list[Definition]:
    """Convert ``ClassDef`` / ``FunctionDef`` / ``AsyncFunctionDef`` found
    inside conditional or ``try`` blocks into ``UNCLASSIFIED`` definitions.
    """
    result: list[Definition] = []
    for inner in nodes:
        if isinstance(inner, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            end_lineno = inner.end_lineno if inner.end_lineno is not None else inner.lineno
            result.append(
                Definition(
                    name=inner.name,
                    kind=DefinitionKind.UNCLASSIFIED,
                    lineno=inner.lineno,
                    end_lineno=end_lineno,
                    source_segment=_segment(source, inner),
                )
            )
    return result


def classify_top_level(tree: ast.Module, source: str) -> tuple[Definition, ...]:
    """Walk a module's top-level body and classify every statement.

    All ``Import`` and ``ImportFrom`` statements in ``tree.body`` are
    collapsed into a single ``IMPORT_BLOCK`` definition regardless of where
    they appear, so the resulting ``SplitPlan`` has at most one
    ``imports.py``. Statements that wrap other definitions (top-level
    ``if`` / ``try``) are themselves ``UNCLASSIFIED`` and the inner
    definitions they wrap are also ``UNCLASSIFIED`` (REQ-ABD-002). The
    return order groups by :class:`DefinitionKind` and preserves source
    order within each group; the canonical order is ``CLASS``,
    ``FUNCTION``, ``CONSTANT``, ``IMPORT_BLOCK``, ``UNCLASSIFIED``.

    Args:
        tree: A parsed :class:`ast.Module`.
        source: The full source text (used to extract source segments).

    Returns:
        A tuple of :class:`Definition` objects grouped by kind, in source
        order within each group.
    """
    import_segments: list[str] = []
    import_start_lineno: int | None = None
    import_end_lineno: int | None = None
    others: list[Definition] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_segments.append(_segment(source, node))
            if import_start_lineno is None:
                import_start_lineno = node.lineno
            import_end_lineno = node.end_lineno if node.end_lineno is not None else node.lineno
            continue

        if isinstance(node, ast.If):
            others.extend(_harvest_inner_unclassified(list(node.body), source))
            others.append(classify_node(node, source))
            continue

        if isinstance(node, ast.Try):
            others.extend(_harvest_inner_unclassified(list(node.body), source))
            others.append(classify_node(node, source))
            continue

        others.append(classify_node(node, source))

    buckets: dict[DefinitionKind, list[Definition]] = {kind: [] for kind in DefinitionKind}
    for definition in others:
        buckets[definition.kind].append(definition)

    if import_start_lineno is not None:
        buckets[DefinitionKind.IMPORT_BLOCK].append(
            Definition(
                name="imports",
                kind=DefinitionKind.IMPORT_BLOCK,
                lineno=import_start_lineno,
                end_lineno=(
                    import_end_lineno if import_end_lineno is not None else import_start_lineno
                ),
                source_segment="\n".join(import_segments),
            )
        )

    result: list[Definition] = []
    for kind in DefinitionKind:
        result.extend(buckets[kind])
    return tuple(result)

"""Module-tree proposal generation.

Given a tuple of classified :class:`Definition` objects, group them into
a :class:`SplitPlan`. The default ``type_based`` strategy yields a fixed
set of module files (``models.py``, ``functions.py``, ``constants.py``,
``imports.py``) plus one ``unclassified_<name>.py`` file per unclassified
definition (REQ-ABD-003).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from cli_app.splitter.classifier import Definition, DefinitionKind

# The only grouping strategy supported in v1.
DEFAULT_STRATEGY: Final[str] = "type_based"


@dataclass(frozen=True, slots=True)
class ModuleProposal:
    """A single proposed module file inside the split package.

    Attributes:
        filename: The module filename (no path component), e.g.
            ``"models.py"``. The package directory is added by the caller.
        definitions: The classified definitions that should live in this
            module. Order matches source order.
    """

    filename: str
    definitions: tuple[Definition, ...]


@dataclass(frozen=True, slots=True)
class SplitPlan:
    """A proposed split of a monolithic Python file into a package.

    Attributes:
        package_name: The proposed package directory name, e.g.
            ``"mylib"``.
        source_path: The path to the source file (kept for traceability
            and for executor code that needs the original location).
        modules: The proposed modules, in canonical order.
        warnings: Non-blocking warnings, e.g. ``"unclassified at line 5"``
            or ``"no top-level definitions found"``.
    """

    package_name: str
    source_path: Path
    modules: tuple[ModuleProposal, ...]
    warnings: tuple[str, ...]


# Fixed module filename per DefinitionKind, in canonical order.
_KIND_TO_FILENAME: Final[dict[DefinitionKind, str]] = {
    DefinitionKind.CLASS: "models.py",
    DefinitionKind.FUNCTION: "functions.py",
    DefinitionKind.CONSTANT: "constants.py",
    DefinitionKind.IMPORT_BLOCK: "imports.py",
}


def _sanitize_module_stem(name: str) -> str:
    """Sanitize a definition name into a valid Python module stem.

    Strips non-identifier characters, lowercases the result, and prefixes
    ``u_`` if the first character is a digit.
    """
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not safe:
        return "unclassified"
    if not (safe[0].isalpha() or safe[0] == "_"):
        safe = f"u_{safe}"
    return safe.lower()


def _warning_for_unclassified(definition: Definition) -> str:
    """Format a warning string for a single unclassified definition."""
    snippet = ""
    if definition.source_segment:
        first_line = definition.source_segment.splitlines()[0]
        snippet = f": {first_line[:60]}"
    return f"unclassified at line {definition.lineno}{snippet}"


def build_proposal(
    definitions: tuple[Definition, ...],
    strategy: str = DEFAULT_STRATEGY,
    *,
    source_path: Path,
    package_name: str,
) -> SplitPlan:
    """Group classified definitions into a :class:`SplitPlan`.

    For the default ``type_based`` strategy the fixed module layout is
    ``models.py`` (classes), ``functions.py`` (functions),
    ``constants.py`` (constants), ``imports.py`` (at most one
    ``IMPORT_BLOCK``). Every unclassified definition gets its own
    ``unclassified_<sanitized_name>.py`` file. Warnings are emitted for
    every unclassified item and for empty input.

    Args:
        definitions: The classified top-level definitions, in the order
            returned by :func:`classify_top_level`.
        strategy: The grouping strategy. Only ``"type_based"`` is
            supported in v1.
        source_path: The path to the source file (for traceability).
        package_name: The proposed package directory name.

    Returns:
        A :class:`SplitPlan` with the proposed module structure and any
        warnings.

    Raises:
        ValueError: If ``strategy`` is not a known strategy.
    """
    if strategy != DEFAULT_STRATEGY:
        raise ValueError(
            f"unknown strategy: {strategy!r} (only {DEFAULT_STRATEGY!r} supported in v1)"
        )

    warnings: list[str] = []
    if not definitions:
        warnings.append("no top-level definitions found")

    by_kind: dict[DefinitionKind, list[Definition]] = {kind: [] for kind in DefinitionKind}
    for definition in definitions:
        by_kind[definition.kind].append(definition)

    modules: list[ModuleProposal] = []
    for kind, filename in _KIND_TO_FILENAME.items():
        bucket = by_kind[kind]
        if bucket:
            modules.append(ModuleProposal(filename=filename, definitions=tuple(bucket)))

    for definition in by_kind[DefinitionKind.UNCLASSIFIED]:
        stem = _sanitize_module_stem(definition.name)
        modules.append(
            ModuleProposal(
                filename=f"unclassified_{stem}.py",
                definitions=(definition,),
            )
        )

    for definition in by_kind[DefinitionKind.UNCLASSIFIED]:
        warnings.append(_warning_for_unclassified(definition))

    return SplitPlan(
        package_name=package_name,
        source_path=source_path,
        modules=tuple(modules),
        warnings=tuple(warnings),
    )

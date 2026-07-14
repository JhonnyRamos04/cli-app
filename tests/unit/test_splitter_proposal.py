"""Unit tests for :mod:`cli_app.splitter.proposal`."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli_app.splitter.classifier import Definition, DefinitionKind
from cli_app.splitter.proposal import (
    DEFAULT_STRATEGY,
    ModuleProposal,
    SplitPlan,
    build_proposal,
)


def _def(name: str, kind: DefinitionKind, lineno: int = 1) -> Definition:
    """Build a synthetic ``Definition`` for proposal tests."""
    return Definition(
        name=name,
        kind=kind,
        lineno=lineno,
        end_lineno=lineno,
        source_segment="",
    )


def test_default_strategy_is_type_based() -> None:
    """``DEFAULT_STRATEGY`` is the only supported strategy in v1."""
    assert DEFAULT_STRATEGY == "type_based"


def test_build_proposal_with_empty_input_emits_warning(tmp_path: Path) -> None:
    """An empty definition list emits the ``no top-level definitions found``
    warning (REQ-ABD-003)."""
    plan = build_proposal(
        (),
        source_path=tmp_path / "empty.py",
        package_name="empty",
    )

    assert isinstance(plan, SplitPlan)
    assert plan.modules == ()
    assert "no top-level definitions found" in plan.warnings


def test_build_proposal_with_single_class_yields_models_py(tmp_path: Path) -> None:
    """A single class lands in ``models.py``."""
    plan = build_proposal(
        (_def("A", DefinitionKind.CLASS, lineno=1),),
        source_path=tmp_path / "x.py",
        package_name="x",
    )

    assert len(plan.modules) == 1
    assert isinstance(plan.modules[0], ModuleProposal)
    assert plan.modules[0].filename == "models.py"
    assert [d.name for d in plan.modules[0].definitions] == ["A"]


def test_build_proposal_with_multi_definitions_groups_each_kind(
    tmp_path: Path,
) -> None:
    """Multiple definitions of different kinds are grouped into their
    canonical module files."""
    defs = (
        _def("A", DefinitionKind.CLASS, lineno=1),
        _def("f", DefinitionKind.FUNCTION, lineno=3),
        _def("B", DefinitionKind.CLASS, lineno=5),
        _def("MAX", DefinitionKind.CONSTANT, lineno=7),
        _def("imports", DefinitionKind.IMPORT_BLOCK, lineno=9),
    )

    plan = build_proposal(defs, source_path=tmp_path / "x.py", package_name="x")

    by_filename = {m.filename: m for m in plan.modules}
    assert "models.py" in by_filename
    assert "functions.py" in by_filename
    assert "constants.py" in by_filename
    assert "imports.py" in by_filename

    assert [d.name for d in by_filename["models.py"].definitions] == ["A", "B"]
    assert [d.name for d in by_filename["functions.py"].definitions] == ["f"]
    assert [d.name for d in by_filename["constants.py"].definitions] == ["MAX"]
    assert [d.name for d in by_filename["imports.py"].definitions] == ["imports"]


def test_build_proposal_omits_empty_kinds(tmp_path: Path) -> None:
    """A module that only has classes does not yield ``functions.py`` etc."""
    plan = build_proposal(
        (_def("A", DefinitionKind.CLASS, lineno=1),),
        source_path=tmp_path / "x.py",
        package_name="x",
    )

    filenames = [m.filename for m in plan.modules]
    assert "functions.py" not in filenames
    assert "constants.py" not in filenames
    assert "imports.py" not in filenames


def test_build_proposal_unclassified_each_gets_own_module(
    tmp_path: Path,
) -> None:
    """Every unclassified definition gets its own module file."""
    defs = (
        _def("unclassified_at_line_1", DefinitionKind.UNCLASSIFIED, lineno=1),
        _def("unclassified_at_line_3", DefinitionKind.UNCLASSIFIED, lineno=3),
    )

    plan = build_proposal(defs, source_path=tmp_path / "x.py", package_name="x")

    unclassified_modules = [
        m
        for m in plan.modules
        if m.filename.startswith("unclassified_") and m.filename.endswith(".py")
    ]
    assert len(unclassified_modules) == 2
    for module in unclassified_modules:
        assert len(module.definitions) == 1


def test_build_proposal_unclassified_emits_warning(tmp_path: Path) -> None:
    """Each unclassified definition contributes a warning (REQ-ABD-002)."""
    defs = (_def("unclassified_at_line_5", DefinitionKind.UNCLASSIFIED, lineno=5),)

    plan = build_proposal(defs, source_path=tmp_path / "x.py", package_name="x")

    assert any("unclassified" in w for w in plan.warnings)
    assert any("line 5" in w for w in plan.warnings)


def test_build_proposal_preserves_source_path_and_package_name(
    tmp_path: Path,
) -> None:
    """``source_path`` and ``package_name`` are surfaced on the plan."""
    src = tmp_path / "x.py"

    plan = build_proposal(
        (_def("A", DefinitionKind.CLASS, lineno=1),),
        source_path=src,
        package_name="x",
    )

    assert plan.source_path == src
    assert plan.package_name == "x"


def test_build_proposal_rejects_unknown_strategy(tmp_path: Path) -> None:
    """An unknown strategy raises ``ValueError``."""
    with pytest.raises(ValueError):
        build_proposal(
            (_def("A", DefinitionKind.CLASS, lineno=1),),
            strategy="random",
            source_path=tmp_path / "x.py",
            package_name="x",
        )

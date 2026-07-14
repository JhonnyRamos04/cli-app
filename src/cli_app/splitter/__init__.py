"""Splitter engine: AST parsing, classification, and module proposal generation.

Public surface re-exports the data model and the main entry points so the
CLI layer never has to reach into the sub-modules directly.
"""

from __future__ import annotations

from cli_app.splitter.classifier import Definition, DefinitionKind
from cli_app.splitter.parser import parse_source
from cli_app.splitter.proposal import (
    DEFAULT_STRATEGY,
    ModuleProposal,
    SplitPlan,
    build_proposal,
)

__all__ = [
    "DEFAULT_STRATEGY",
    "Definition",
    "DefinitionKind",
    "ModuleProposal",
    "SplitPlan",
    "build_proposal",
    "parse_source",
]

# external-compatibility Specification

## Purpose

Ensure consumers of the original module can still import its public API after the split by generating `__init__.py` re-exports and offering an optional project-wide import-rewrite pass.

## Requirements

### REQ-EXT-001: __init__.py Re-Exports

The system SHALL generate `__init__.py` in the new package directory that re-exports every public definition from each split module using `from .module import Name` syntax.

#### Scenario: Re-export all public symbols

- GIVEN split modules `models.py` (class `User`) and `utils.py` (function `validate`)
- WHEN `__init__.py` is generated
- THEN it contains `from .models import User` and `from .utils import validate`
- AND `from original_module import User` continues to work for external consumers

#### Scenario: Private symbol exclusion

- GIVEN `models.py` defines `_InternalHelper` (prefixed with underscore)
- WHEN `__init__.py` is generated
- THEN `_InternalHelper` is NOT re-exported
- AND only public symbols (no leading underscore) appear in re-exports

### REQ-EXT-002: Opt-In Global Import Rewrite

The system MAY offer an optional pass that scans the broader project directory (or a user-specified path) and rewrites `from {original_module} import X` to `from {original_module}.{submodule} import X` for symbols that now live in a specific submodule. This pass SHALL NOT execute without the user passing an explicit `--project <path>` flag.

#### Scenario: User opts into project-wide rewrite

- GIVEN a `main.py` in the same directory imports `from mylib import User`, and `User` now lives in `mylib/models.py`
- WHEN the user runs `reconcile` with `--project .`
- THEN `from mylib import User` is rewritten to `from mylib.models import User`
- AND a backup `main.py.bak` is created before modification

#### Scenario: User does NOT opt into project-wide rewrite

- GIVEN the `--project` flag is not passed
- WHEN the reconciler runs
- THEN only the split package files are modified
- AND no files outside the package are touched

### REQ-EXT-003: Dry-Run for Global Rewrite

When `--project` is passed, the system SHALL first display a diff of all planned changes and SHALL require confirmation before writing.

#### Scenario: Dry-run preview with confirmation

- GIVEN `--project .` and three files would be modified
- WHEN the reconciler runs
- THEN a diff for each file is displayed
- AND the user is prompted for confirmation before any writes

## Cross-Platform Notes

- `__init__.py` SHALL be written with `encoding="utf-8"` and LF line endings per AGENTS.md.
- Project-wide glob traversal MUST use `pathlib.Path.rglob("*.py")` — never `os.walk` or string paths.

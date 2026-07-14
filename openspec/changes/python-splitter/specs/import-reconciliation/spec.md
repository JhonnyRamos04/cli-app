# import-reconciliation Specification

## Purpose

After splitting the monolith into a package, rewrite intra-package references so that imports between the new modules resolve correctly.

## Requirements

### REQ-IRC-001: Intra-Package Import Rewriting

The system SHALL scan every split module file and rewrite references to definitions that have moved to other modules within the same package. Rewritten imports SHALL use relative import syntax (e.g., `from .models import User`).

#### Scenario: Class moved to sibling module

- GIVEN `utils.py` contains `validate(user: User)` referencing class `User`, which now lives in `models.py`
- WHEN the reconciler processes `utils.py`
- THEN `from models import User` (original) is rewritten to `from .models import User`
- AND all other imports in `utils.py` are left unchanged

#### Scenario: No cross-references between modules

- GIVEN a split where `models.py` and `constants.py` share no references to each other
- WHEN the reconciler processes both files
- THEN no import lines are added or modified
- AND each file's content is byte-identical to its post-split state

### REQ-IRC-002: Undefined Reference Detection

The system SHALL detect references to symbols that were NOT defined in the original monolith and SHALL NOT exist in any split module. These SHALL be reported as warnings but SHALL NOT block the reconciliation.

#### Scenario: Reference to external library

- GIVEN `utils.py` imports `from dataclasses import dataclass` and uses `@dataclass`
- WHEN the reconciler scans `utils.py`
- THEN `dataclass` is recognized as external (stdlib) and not rewritten
- AND no warning is emitted

#### Scenario: Reference to undefined symbol

- GIVEN `utils.py` references `helper` which was never defined in the original file
- WHEN the reconciler processes `utils.py`
- THEN a warning is emitted: "unresolved reference 'helper' in utils.py at line N"
- AND reconciliation continues for other files

### REQ-IRC-003: Import Block Preservation

The system SHALL NOT alter import lines that reference external libraries or standard-library modules. Only imports targeting definitions that moved within the package SHALL be rewritten.

#### Scenario: Mixed imports

- GIVEN a file with `import os`, `from typing import List`, and `from original import Foo`
- WHEN `Foo` has moved to `.models`
- THEN `import os` and `from typing import List` are preserved exactly
- AND `from original import Foo` is rewritten to `from .models import Foo`

## Cross-Platform Notes

- File reading and writing MUST use `encoding="utf-8"` with `pathlib.Path`.
- The reconciler operates on files already written to disk — path resolution MUST use `pathlib.Path` for all intra-package lookups.

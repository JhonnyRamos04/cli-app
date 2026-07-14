# split-execution Specification

## Purpose

Execute the approved module split: create a package directory, write each proposed module file, generate `__init__.py`, and preserve a backup of the original source.

## Requirements

### REQ-SEX-001: Package Directory Creation

The system SHALL create a new directory named after the source file's stem (e.g., `mylib.py` → `mylib/`) adjacent to the source file, and SHALL create an `__init__.py` inside it.

#### Scenario: Fresh split of a single-file module

- GIVEN `mylib.py` containing class `Foo` and function `bar`, with `models.py` and `utils.py` proposed
- WHEN the split executes
- THEN `mylib/__init__.py`, `mylib/models.py`, and `mylib/utils.py` are created
- AND a backup `mylib.py.bak` is written

#### Scenario: Target directory already exists

- GIVEN `mylib/` already exists on disk
- WHEN the split attempts to create the package directory
- THEN an error is raised: "directory 'mylib/' already exists — aborting"
- AND no files inside the existing directory are modified
- AND the exit code is non-zero

### REQ-SEX-002: Module File Content Generation

The system SHALL write each proposed module file with the correct source text for its assigned definitions, extracted verbatim from the original source. Each module file SHALL include the necessary imports copied from the original's import block.

#### Scenario: Module with class and its dependencies

- GIVEN original imports include `from dataclasses import dataclass` and class `User` is assigned to `models.py`
- WHEN `models.py` is written
- THEN the file begins with `from dataclasses import dataclass`
- AND the `User` class definition follows verbatim

#### Scenario: Module with only constants

- GIVEN module `constants.py` has no class or function definitions
- WHEN the file is written
- THEN it contains only the constant assignments extracted from the original
- AND no import block is prefixed unless the constants reference imported symbols

### REQ-SEX-003: Backup and Rollback

The system SHALL write a byte-for-byte backup of the original file to `{filename}.bak` BEFORE any new files are created. If any write fails during split, the system SHALL restore the backup and remove partial output.

#### Scenario: Write failure mid-split

- GIVEN disk space is exhausted after writing `mylib/__init__.py` but before `mylib/models.py`
- WHEN the write for `models.py` fails with `OSError`
- THEN the backup `mylib.py.bak` is restored to `mylib.py`
- AND the partial `mylib/` directory is removed
- AND the error is reported to stderr

## Cross-Platform Notes

- All file writes MUST use `Path.write_text(data, encoding="utf-8")` per AGENTS.md.
- Directory creation MUST use `Path.mkdir(parents=True, exist_ok=False)`.
- Written files SHALL use LF line endings — never CRLF.
- Backup SHALL be a byte-copy (`Path.read_bytes()` → `Path.write_bytes()`) to preserve exact encoding and line endings.

# cli-interface Specification

## Purpose

Expose the splitter and reconciler as a Typer CLI application with `split` and `reconcile` subcommands, rich-formatted output, and cross-platform compatibility.

## Requirements

### REQ-CLI-001: Typer App Registration

The system SHALL define a `typer.Typer` instance as the CLI entry point in `src/cli_app/cli.py`. Commands SHALL be registered as decorated functions using `@app.command()`. Every command function SHALL have a docstring used as `--help` text.

#### Scenario: `--help` on root app

- GIVEN the CLI is installed via `pip install -e .`
- WHEN the user runs `cli-app --help`
- THEN output lists `split` and `reconcile` as available commands
- AND each command shows its one-line docstring summary

### REQ-CLI-002: `split` Command

The system SHALL provide a `split` command with the following signature:

```
cli-app split SOURCE [--yes/-y] [--output-dir DIR]
```

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes (positional) | Path to the monolithic `.py` file |
| `--yes` / `-y` | No | Skip confirmation prompt |
| `--output-dir` | No | Directory for the split package (default: adjacent to SOURCE) |

#### Scenario: Happy path — split with confirmation

- GIVEN `mylib.py` exists and is valid Python
- WHEN the user runs `cli-app split mylib.py`
- THEN the AST analysis runs
- AND the module tree preview is rendered via `rich.tree`
- AND the user is prompted to confirm
- AND on confirmation, the split executes

#### Scenario: Non-existent source file

- GIVEN `nonexistent.py` does not exist
- WHEN the user runs `cli-app split nonexistent.py`
- THEN an error is displayed: "file not found: nonexistent.py"
- AND the exit code is non-zero

#### Scenario: Source is not a Python file

- GIVEN `data.txt` exists but is not a `.py` file
- WHEN the user runs `cli-app split data.txt`
- THEN an error is displayed: "not a Python file: data.txt"
- AND the exit code is non-zero

### REQ-CLI-003: `reconcile` Command

The system SHALL provide a `reconcile` command with the following signature:

```
cli-app reconcile PACKAGE_DIR [--project PATH]
```

| Argument | Required | Description |
|---|---|---|
| `PACKAGE_DIR` | Yes (positional) | Path to the split package directory |
| `--project` | No | Path to project root for global import rewrite |

#### Scenario: Reconcile without project flag

- GIVEN a split package at `mylib/` with unresolved intra-package imports
- WHEN the user runs `cli-app reconcile mylib`
- THEN intra-package imports are rewritten
- AND no files outside `mylib/` are touched

#### Scenario: Reconcile with project flag

- GIVEN `--project .` and external `main.py` imports from the split package
- WHEN the user runs `cli-app reconcile mylib --project .`
- THEN a diff of planned changes to `main.py` is displayed
- AND the user is prompted to confirm before writes

### REQ-CLI-004: Rich Output

The system SHALL use `rich` for all formatted output: `rich.console.Console` for styled text, `rich.tree` for module tree previews, and `rich.table` for tabular data. On Windows terminals without ANSI support, rich SHALL fall back to plain text automatically.

#### Scenario: Module tree rendered with rich

- GIVEN a split proposal
- WHEN the preview is displayed
- THEN the module tree uses `rich.tree` with colored node labels
- AND on a non-ANSI terminal, rich degrades to plain ASCII

## Cross-Platform Notes

- The CLI entry point in `pyproject.toml` (`[project.scripts] cli-app = "cli_app.cli:app"`) enables `cli-app` on PATH on both Windows and Linux per AGENTS.md.
- The `__main__.py` SHALL include `#!/usr/bin/env python3` for Linux deployment per AGENTS.md executable-entry-point rule.
- All path arguments SHALL be resolved with `pathlib.Path` — never string concatenation.

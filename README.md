# cli-app

A Python CLI that splits monolithic Python files into structured packages and
reconciles their imports. Built on `typer` for the command surface and `rich`
for output.

## Status

`ast-boundary-detection` (PR 1). The `split` and `reconcile` commands are
stubs at this stage; the splitter engine can parse and classify a `.py` file
into a `SplitPlan` but does not yet write to disk.

## Install (development)

```sh
python -m venv .venv
. .venv/Scripts/Activate.ps1   # Windows
# . .venv/bin/activate         # Linux/macOS
pip install -e ".[dev]"
```

## Usage

```sh
cli-app --help
cli-app split --help
cli-app reconcile --help
```

## Quality gates

```sh
ruff check .
ruff format --check .
mypy src tests
pytest
```

## Cross-platform

All paths use `pathlib.Path`, all file I/O uses `encoding="utf-8"`, and every
text file is LF. See `AGENTS.md` for the full baseline.

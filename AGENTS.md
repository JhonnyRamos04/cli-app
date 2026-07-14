# AGENTS.md

> Conventions for AI agents and human contributors working on `cli-app` — a Python 3.11+ CLI app developed on Windows, deployed to Linux.

## What this project is

- **Stack**: Python 3.11+, `typer` for the CLI, `rich` for output, `pytest` for tests, `ruff` for lint+format, `mypy` strict for types.
- **Layout**: `src/cli_app/` source, `tests/` mirrored, `pyproject.toml` as the single source of truth for config.
- **The first app**: a Python code **splitter/reconciler**. Uses the `ast` module to propose module boundaries in a monolithic `.py` file, shows the plan, and on confirmation splits into a package and rewrites imports.
- **Workflow**: session-level OpenSpec (`openspec/`). Check for an active change in `openspec/changes/` before touching `src/`.
- **History of key decisions**: see Engram topic `architecture/splitter-strategy` and `sdd-init/cli-app/preflight`.

## Quick path for an agent

1. Read `openspec/config.yaml` and any active change in `openspec/changes/`.
2. Read the relevant code in `src/cli_app/` before writing.
3. Make the change. Follow every rule below.
4. Run: `ruff check . && ruff format --check . && mypy src tests && pytest`.
5. Commit with conventional format (see [Conventional Commits](#conventional-commits)).
6. If you discovered a non-obvious decision, save it to Engram via `mem_save` with `project: cli-app`.

## Cross-platform baseline (Windows dev → Linux deploy)

Every line below has broken a deployment at least once. Don't argue, follow it.

| Rule | Why | Concrete how |
| --- | --- | --- |
| All text files MUST be LF, never CRLF | CRLF breaks shell scripts, causes diff churn, surprises on Linux clones | `.gitattributes` with `* text=auto eol=lf`; never commit CRLF |
| Executable Python entry points MUST have `#!/usr/bin/env python3` | Windows ignores it, Linux requires it | First line of any `__main__.py`; for `console_scripts` in `pyproject.toml` it is auto |
| Use `pathlib.Path`, never string concat with `\` or `/` | Backslashes are illegal in Linux paths, forward slashes work on both | `Path(base) / "sub" / "file.txt"` |
| Always pass `encoding="utf-8"` to `open`, `Path.read_text`, `Path.write_text` | Windows defaults to `cp1252`, Linux to `utf-8` — explicit removes the ambiguity | Never `open(path)` without `encoding=...` |
| Set executable bit via git, not `os.chmod` | `os.chmod` is a no-op on Windows for the user bit and inconsistent across filesystems | `git update-index --chmod=+x path/to/script` records the intent for Linux clones |
| Never use `subprocess.run(..., shell=True)` with a hardcoded command | `shell=True` invokes `cmd.exe` on Windows, `sh` on Linux — different parsing rules, different PATH expansion | `subprocess.run(["prog", "arg"], check=True)` with a list |
| Read env vars with explicit defaults | `HOME` on Windows is `C:\Users\...`, on Linux `/home/...`; `PATH` separator differs | `os.environ.get("KEY", default)`; never assume `~/.config` is a valid path on both |
| Use `Path` for tmp dirs in tests, not `tempfile.mkdtemp` with manual cleanup | `mkdtemp` works but `tmp_path` fixture handles Windows ACLs and cleanup automatically | `def test_x(tmp_path: Path) -> None:` |
| File modes in `os.open` are advisory on Windows | Cross-platform permissions are unreliable — track the executable bit in git, validate behaviour in code | Avoid `os.chmod`; use `git update-index --chmod=+x` |
| Line endings in source code: assert with `pathlib`'s `.read_bytes()` then decode explicitly if you must detect them | `open(..., "r")` strips the difference on `text=` files | Use `git ls-files --eol` to verify a clean tree |

## Project structure

```
cli-app/
├── pyproject.toml          # single source of truth: deps, tool config, entry points
├── AGENTS.md               # this file
├── README.md               # human-facing overview (separate from this file)
├── .gitattributes          # * text=auto eol=lf
├── .gitignore              # python venvs, __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, dist/, build/
├── .pre-commit-config.yaml # recommended for humans, optional for agents
├── src/
│   └── cli_app/
│       ├── __init__.py
│       ├── __main__.py     # enables `python -m cli_app` as a fallback
│       ├── cli.py          # typer app + command definitions
│       ├── splitter/       # AST analysis + boundary proposal
│       ├── reconciler/     # import-rewriter + reference fixup
│       └── _internal/      # private helpers, not part of the public API
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

### `pyproject.toml` rules

- Use `[build-system]` with `hatchling` (default for new Python projects in 2026). No `setup.py`, no `setup.cfg`, no `requirements.txt` for app deps.
- App deps go in `[project] dependencies = [...]`. Dev deps in `[project.optional-dependencies] dev = [...]`.
- Entry points under `[project.scripts]` so `pip install -e .` puts the CLI on `PATH` (works on Windows and Linux):
  ```toml
  [project.scripts]
  cli-app = "cli_app.cli:app"
  ```
  `app` here is the `typer.Typer` instance.
- All tool config (ruff, mypy, pytest, coverage) lives under `[tool.<name>]` in the same file.

## CLI framework: Typer

- **Typer is the default.** Type-hint driven, built on Click, great `--help`, works on Windows + Linux out of the box.
- **Click** is acceptable for libraries that must stay framework-agnostic. Do not use it for a user-facing app unless there's a reason.
- **`argparse`** is acceptable ONLY for stdlib-only scripts. Never for a user-facing app.
- Every command MUST have a docstring — Typer uses it for `--help` text.
- Use `rich` (already a Typer dep) for structured output: tables, panels, progress bars. On Windows terminals without ANSI, rich auto-falls back to plain text.
- The CLI app is an instance: `app = typer.Typer()` in `src/cli_app/cli.py`. Subcommands register on it. Do not instantiate Typer per command.

## Testing (pytest)

- `pytest` is the framework. Configured in `pyproject.toml` under `[tool.pytest.ini_options]`.
- Test layout: `tests/unit/` for pure logic (no I/O, no network), `tests/integration/` for I/O, file system, subprocess.
- Test files: `test_*.py`. Test functions: `test_*`. Test classes: `Test*`.
- Use `tmp_path` fixture (NOT `tempfile.mkdtemp`) — cross-platform cleanup.
- Use `monkeypatch` for env vars, not `os.environ` mutation. Cleanup is automatic.
- Use `pytest.param(..., id="...")` to give parametrized cases readable names.
- Coverage: target 80% lines, configured in `[tool.coverage.report]`. Don't game the number — exclude `pragma: no cover` only with a justifying comment.
- **NEVER** `@pytest.mark.skipif(sys.platform == "win32")` to dodge a Windows-specific failure. Fix the test or guard the code path. The CI runs on Linux; you will not see the failure there.

## Quality tools (configured in `pyproject.toml`)

| Tool | Purpose | Config section | Run |
| --- | --- | --- | --- |
| `ruff` | lint + format (single tool, fast) | `[tool.ruff]`, `[tool.ruff.format]` | `ruff check .` then `ruff format .` |
| `mypy` | static type checking, strict mode | `[tool.mypy]` with `strict = true` | `mypy src tests` |
| `pytest` | tests + coverage | `[tool.pytest.ini_options]`, `[tool.coverage.*]` | `pytest` |

- Run order before declaring a task done: `ruff check .` → `ruff format --check .` → `mypy src tests` → `pytest`.
- Every public function MUST have type hints. `mypy --strict` will reject the code otherwise.
- Line length: 100 (configured in `[tool.ruff] line-length = 100`).
- Imports sorted by `ruff` (isort rules built-in, set `[tool.ruff.lint.isort] known-first-party = ["cli_app"]`).

## Conventional Commits

**Format**: `<type>(<scope>): <description>`

- Lowercase type. Lowercase scope. No period at the end. Imperative mood ("add" not "added").
- Wrap body at 72 chars. Explain **why**, not what (the diff shows what).
- Reference issues in the footer: `Closes #N` or `Refs #N`.

**Allowed types**

| Type | Use for |
| --- | --- |
| `feat` | new user-visible feature |
| `fix` | bug fix |
| `docs` | docs only (including this file) |
| `style` | formatting, no logic change |
| `refactor` | code change that neither fixes a bug nor adds a feature |
| `perf` | performance improvement |
| `test` | add or fix tests only |
| `build` | build system or external deps |
| `ci` | CI config |
| `chore` | tooling, deps, meta — no src/ or test/ change |
| `revert` | revert a previous commit |

**Scopes for this project**: `splitter`, `reconciler`, `cli`, `deps`, `docs`, `tests`, `config`, `agents`.

**Breaking changes**: add `!` after the type/scope AND a `BREAKING CHANGE:` footer that explains the migration.

**Examples**

```
feat(splitter): add ast-based boundary detection
fix(cli): handle missing file argument with friendly error
docs(agents): document line-ending convention
chore(deps): pin typer to ^0.12
refactor(reconciler): split import-rewriter into own module
perf(splitter): cache ast.parse result across proposals
test(reconciler): cover import-rewrite for relative imports
```

## What AI agents MUST do

- Read `openspec/config.yaml` and any active change in `openspec/changes/` before touching `src/`.
- Run `ruff check . && ruff format --check . && mypy src tests && pytest` before declaring a task done.
- Save non-obvious decisions, bug root causes, and conventions to Engram via `mem_save` with `project: cli-app`. Use stable `topic_key` for evolving topics.
- Match `openspec/config.yaml` `testing.command` when running tests. Don't invent a different command.
- Use the skill registry at `.atl/skill-registry.md` to find which skills to load for a sub-agent delegation. Pass only the exact `SKILL.md` paths to the sub-agent — never summarized rules.

## What AI agents MUST NOT do

- Do not add `Co-Authored-By` lines, AI attribution, or any signature other than the conventional commit subject. Period.
- Do not commit secrets, `.env`, credentials, `.venv/`, `__pycache__/`, or build artefacts.
- Do not use `os.system`, `subprocess.run(shell=True)`, or any shell-injection-prone API without explicit user approval.
- Do not skip, `@pytest.mark.xfail`, or delete a test to make CI green. Fix the code or update the test deliberately with a justification in the commit body.
- Do not push to `main` directly. Use a feature branch and a PR.
- Do not modify `.atl/` (local Atlantis cache), `openspec/config.yaml` without an `sdd-init` or `sdd-archive` phase, or any locked file the user has marked out of bounds.
- Do not use `os.chmod` to set executable bits — use `git update-index --chmod=+x` so the intent is recorded in git for Linux clones.
- Do not assume `/tmp` exists. On Windows, use `tempfile.gettempdir()` or the `tmp_path` pytest fixture.

## Reviewer checklist (apply before pushing a PR)

- [ ] PR title is a single conventional commit subject.
- [ ] Each commit in the PR is a single conventional commit subject.
- [ ] No `Co-Authored-By` lines.
- [ ] No secrets, no `.env`, no build artefacts in the diff.
- [ ] `ruff check .` is clean.
- [ ] `ruff format --check .` is clean.
- [ ] `mypy src tests` is clean (strict mode).
- [ ] `pytest` is green. New code has tests.
- [ ] Public functions have type hints.
- [ ] New public symbols are exported in `src/cli_app/__init__.py` only if they are part of the stable API.
- [ ] Cross-platform rules above are respected (paths, encoding, line endings, no `shell=True`).
- [ ] PR is under 400 changed lines (the review budget). If not, see the chained-PR skill.

## Next step

After reading this file, an agent should:

1. Check `openspec/config.yaml` for session preflight.
2. Look for an active change in `openspec/changes/`. If there is one, read it.
3. If there is none and the user gave a new request, run `/sdd-new` (or the equivalent in your orchestrator).

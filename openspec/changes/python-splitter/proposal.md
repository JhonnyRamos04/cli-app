# Proposal: Python Code Splitter/Reconciler

## Intent

Provide a CLI tool that splits monolithic Python files into structured packages. Given a `.py` file, the tool uses `ast` to propose module boundaries (top-level classes, functions, constants), shows the plan for confirmation, then executes the split and reconciles imports to keep everything connected.

## Scope

### In Scope
- AST-based boundary detection (classes, functions, constants/import blocks)
- Interactive plan preview with proposed module tree + sample diff
- Split execution: monolith → package with `__init__.py` re-exports
- Import reconciliation: rewrite internal references across split modules
- External compatibility shim (re-exports + opt-in project-wide import rewrite)
- Typer CLI with `split` and `reconcile` subcommands, `rich` output

### Out of Scope
- Linting, formatting, or type-checking the split output
- Automatic git commit or migration of consumer projects
- GUI or web interface
- Non-Python language support

## Capabilities

### New Capabilities
- `ast-boundary-detection`: Parse Python files with `ast`, group top-level definitions into module proposals
- `split-plan-preview`: Render proposed module tree + diff before user confirms
- `split-execution`: Split source file into a package directory with `__init__.py`
- `import-reconciliation`: Rewrite intra-package imports to match new module structure
- `external-compatibility`: `__init__.py` re-exports + opt-in global import rewriting
- `cli-interface`: Typer CLI with `split`/`reconcile` commands, help, rich table output

### Modified Capabilities
None — greenfield change. No existing specs to modify.

## Approach

Hybrid AST-proposes-user-confirms (see Engram `architecture/splitter-strategy`). The splitter scans source with Python's `ast`, groups declarations by type, proposes a module layout; user reviews and confirms. On confirmation, splitter creates the package structure and reconciler rewrites imports. The reconciler generates `__init__.py` re-exports and offers an optional pass to update imports in the broader project. Dry-run mode is default — user must explicitly confirm before any write.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/cli_app/cli.py` | New | Typer app with split/reconcile commands |
| `src/cli_app/splitter/` | New | AST analysis + boundary proposal engine |
| `src/cli_app/reconciler/` | New | Import rewriting + reference fixup |
| `src/cli_app/_internal/` | New | Shared helpers (path resolution, dry-run, backup) |
| `pyproject.toml` | Modified | Add typer/rich deps, CLI entry point, tool config |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| AST edge cases (decorated classes, conditional defs) | Medium | Unit-test against real Python files; fallback to "unclassified" bucket |
| Cross-platform path encoding | Low | `pathlib` everywhere; never concat paths as strings |
| No undo after user confirms | Low | Prompt shows preview + diff before write; backup original first |

## Rollback Plan

- The splitter creates a backup copy at `{filename}.bak` before any write
- On error or abort, restore backup and remove partial output directories
- The reconciler operates on copies — originals never mutated without backup

## Dependencies

- Python stdlib: `ast`, `pathlib`
- External: `typer`, `rich` (add to `pyproject.toml`)
- No runtime dependencies beyond typer and rich

## Success Criteria

- [ ] `cli-app split some_file.py` parses a real .py file and shows a valid module proposal
- [ ] On confirm, split produces a working package: all internal imports resolve
- [ ] External compat: `from original_module import Thing` still works after split
- [ ] Test suite covers boundary detection, split execution, and import rewriting
- [ ] `ruff check . && ruff format --check . && mypy src tests && pytest` passes clean

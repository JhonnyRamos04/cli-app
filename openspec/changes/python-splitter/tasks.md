# Tasks: Python Code Splitter/Reconciler

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated total changed lines | ~1,200 |
| 400-line budget risk | **High** (whole; Low per PR) |
| Chained PRs recommended | **Yes** |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### PR Slicing

| PR | Unit | Est. Lines | Delivers | Base |
|----|------|------------|----------|------|
| 1 | Bootstrap + splitter core | ~330 | `pyproject.toml`, CLI entry, parser, classifier; unit tests | main (or tracker) |
| 2 | Proposal + executor + CLI wiring | ~370 | `cli-app split foo.py` end-to-end with preview + confirm | PR 1 |
| 3 | Reconciler intra-package engine | ~280 | `cli-app reconcile mylib/` rewrites imports | PR 2 |
| 4 | Project-wide pass + fixtures + polish | ~240 | `--project` flag, integration tests, edge-case fixtures | PR 3 |

Justification: parser+classifier is the foundation (PR 1). Proposal+executor builds on it to deliver the first usable command (PR 2). Reconciler imports+references is independent enough to be PR 3. Project-wide pass is the most speculative and has the heaviest integration tests — isolating it in PR 4 keeps earlier PRs reviewable.

## PR 1: Bootstrap + Parser + Classifier (~330 lines)

**Delivers**: Installable CLI with `--help`, AST parsing and top-level classification, unit-test coverage for parser and classifier. No file writes.

- [ ] 1.1 `build(config): add pyproject.toml with hatchling, typer+rich deps, ruff/mypy/pytest config` — `pyproject.toml`, `.gitattributes` — REQ-CLI-001 entry point
- [ ] 1.2 `feat(cli): create typer app entry point with split/reconcile stubs and __main__` — `src/cli_app/__init__.py`, `__main__.py`, `cli.py` — REQ-CLI-001, REQ-CLI-002 sig, REQ-CLI-003 sig
- [ ] 1.3 `feat(splitter): add parser with parse_source and classify_node` — `src/cli_app/splitter/__init__.py`, `parser.py` (DefinitionKind enum, parse_source, classify_node) — REQ-ABD-001
- [ ] 1.4 `feat(splitter): add classifier with classify_top_level and Definition dataclass` — `src/cli_app/splitter/classifier.py` — REQ-ABD-001 (order, decorated), REQ-ABD-002 (unclassified via If/Expr)
- [ ] 1.5 `feat(splitter): add internal paths helper with resolve_source and package_dir_for` — `src/cli_app/_internal/__init__.py`, `paths.py` — design: paths contract
- [ ] 1.6 `test(splitter): add unit tests for parser — inline ast strings, utf-8, syntax error` — `tests/conftest.py`, `tests/unit/test_parser.py` — REQ-ABD-001 scenarios
- [ ] 1.7 `test(splitter): add unit tests for classifier — ClassDef, FunctionDef, AsyncFunctionDef, Assign, If/TYPE_CHECKING, Expr` — `tests/unit/test_classifier.py` — REQ-ABD-001, REQ-ABD-002 scenarios

## PR 2: Proposal + Executor + CLI Wiring (~370 lines)

**Delivers**: `cli-app split foo.py` is fully usable — parses, classifies, proposes layout, renders rich.tree preview, confirms, backs up original, writes package.

- [ ] 2.1 `feat(splitter): add proposal engine with build_proposal and SplitPlan/ModuleProposal` — `src/cli_app/splitter/proposal.py` — REQ-ABD-003 (type-based grouping, empty file warning)
- [ ] 2.2 `feat(splitter): add backup module with write_backup and restore_backup byte-copy` — `src/cli_app/_internal/backup.py` — REQ-SEX-003
- [ ] 2.3 `feat(cli): add confirm helper with confirm_or_exit wrapping typer.confirm` — `src/cli_app/_internal/confirm.py` — REQ-SPP-003
- [ ] 2.4 `feat(splitter): add executor with execute_split creating package dir + __init__.py re-exports + module files` — `src/cli_app/splitter/executor.py` — REQ-SEX-001, REQ-SEX-002, REQ-EXT-001
- [ ] 2.5 `feat(cli): wire split command with parse→classify→propose→preview(rich.tree+difflib)→confirm→execute pipeline` — update `src/cli_app/cli.py` — REQ-SPP-001, REQ-SPP-002, REQ-CLI-002, REQ-CLI-004
- [ ] 2.6 `test(splitter): add unit tests for proposal — grouping, empty, unclassified warnings` — `tests/unit/test_proposal.py` — REQ-ABD-003 scenarios
- [ ] 2.7 `test(splitter): add unit tests for backup — write, restore, byte-identical roundtrip` — `tests/unit/test_backup.py` — REQ-SEX-003
- [ ] 2.8 `test(splitter): add integration test for split happy path — tmp_path, CliRunner, verify package structure + __init__.py + .bak` — `tests/integration/test_split_happy_path.py` — REQ-SEX-001, REQ-SEX-002, REQ-CLI-002
- [ ] 2.9 `test(splitter): add integration test for split rollback — mock OSError mid-write, verify restore + cleanup` — `tests/integration/test_split_rollback.py` — REQ-SEX-003

## PR 3: Reconciler Intra-Package Engine (~280 lines)

**Delivers**: `cli-app reconcile mylib/` rewrites intra-package imports with relative syntax, detects unresolved references, emits warnings, no files outside package touched.

- [ ] 3.1 `feat(reconciler): add import rewriter with rewrite_imports and symbol_to_module_map` — `src/cli_app/reconciler/__init__.py`, `imports.py` — REQ-IRC-001, REQ-IRC-003
- [ ] 3.2 `feat(reconciler): add reference detector with detect_unresolved` — `src/cli_app/reconciler/references.py` — REQ-IRC-002
- [ ] 3.3 `feat(cli): wire reconcile command with intra-package pass and rich.table output` — update `src/cli_app/cli.py`, `__init__.py` — REQ-CLI-003, REQ-CLI-004
- [ ] 3.4 `test(reconciler): add unit tests for import rewriter — relative rewrite, mixed imports preserved, no-op` — `tests/unit/test_imports.py` — REQ-IRC-001, REQ-IRC-003
- [ ] 3.5 `test(reconciler): add unit tests for reference detector — stdlib passthrough, unresolved warning` — `tests/unit/test_references.py` — REQ-IRC-002
- [ ] 3.6 `test(reconciler): add integration test for reconcile intra-package — tmp_path split then reconcile, verify imports` — `tests/integration/test_reconcile_intra_package.py` — REQ-IRC-001, REQ-CLI-003

## PR 4: Project-Wide Pass + Fixtures + Polish (~240 lines)

**Delivers**: `cli-app reconcile mylib/ --project .` with diff preview + confirmation. Edge-case fixtures for SQLAlchemy/attrs/Pydantic/TYPE_CHECKING/try-except/exec.

- [ ] 4.1 `feat(reconciler): add project-wide rewriter with rewrite_project_imports, ProjectDiff, apply_project_diff` — `src/cli_app/reconciler/project.py` — REQ-EXT-002, REQ-EXT-003
- [ ] 4.2 `feat(cli): wire reconcile --project flag with rglob, diff preview via difflib+rich, confirm-then-apply` — update `src/cli_app/cli.py` — REQ-EXT-002, REQ-EXT-003
- [ ] 4.3 `test(reconciler): add integration test for reconcile --project flag — dry-run diff, confirm, apply, .bak rollback` — `tests/integration/test_reconcile_project_flag.py` — REQ-EXT-002, REQ-EXT-003
- [ ] 4.4 `test(reconciler): add cross-cutting fixtures for edge-case patterns` — `tests/integration/fixtures/{sqlalchemy_model,attrs_define,pydantic_basemodel,type_checking_block,try_except_class,exec_call}.py` — design R1 mitigation, Q2 fixtures
- [ ] 4.5 `test(config): add conftest fixture_path helper for integration tests` — update `tests/conftest.py` — testing infrastructure

## Verification Plan

| PR | Commands (run before declaring done) |
|----|--------------------------------------|
| 1 | `ruff check . && ruff format --check . && mypy src tests && pytest tests/unit/test_parser.py tests/unit/test_classifier.py` |
| 2 | `ruff check . && ruff format --check . && mypy src tests && pytest tests/unit/test_proposal.py tests/unit/test_backup.py tests/integration/test_split_happy_path.py tests/integration/test_split_rollback.py` |
| 3 | `ruff check . && ruff format --check . && mypy src tests && pytest tests/unit/test_imports.py tests/unit/test_references.py tests/integration/test_reconcile_intra_package.py` |
| 4 | `ruff check . && ruff format --check . && mypy src tests && pytest` (full suite) |

# python-splitter Specs

Six new capability specifications for the Python Code Splitter/Reconciler.

| Capability | Description |
|---|---|
| [`ast-boundary-detection`](./ast-boundary-detection/spec.md) | Parse `.py` files with `ast`, classify top-level definitions, produce module-proposal map |
| [`split-plan-preview`](./split-plan-preview/spec.md) | Render proposed module tree + sample diff via `rich`, prompt user for confirmation |
| [`split-execution`](./split-execution/spec.md) | Create package directory, write module files, generate `__init__.py`, backup original |
| [`import-reconciliation`](./import-reconciliation/spec.md) | Rewrite intra-package imports to relative syntax, detect unresolved references |
| [`external-compatibility`](./external-compatibility/spec.md) | `__init__.py` re-exports + opt-in project-wide import rewrite with dry-run |
| [`cli-interface`](./cli-interface/spec.md) | Typer CLI with `split` and `reconcile` commands, rich output, cross-platform compat |

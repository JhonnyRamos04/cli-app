# ast-boundary-detection Specification

## Purpose

Parse a monolithic Python source file with `ast`, classify its top-level definitions, and produce a structured module-proposal map that the split-plan-preview and split-execution capabilities consume.

## Requirements

### REQ-ABD-001: Parse and Classify Top-Level Definitions

The system SHALL parse a `.py` file using Python's `ast` module and classify every top-level definition into one of these categories: `class`, `function`, `constant`, `import_block`, or `unclassified`.

#### Scenario: Mixed top-level definitions

- GIVEN a Python file containing two classes, three top-level functions, and a module-level constant
- WHEN the parser analyzes the file
- THEN the output groups definitions by category
- AND the order of definitions within each category matches the source order

#### Scenario: Decorated class or function

- GIVEN a Python file with a `@dataclass`-decorated class and a `@staticmethod`-decorated function
- WHEN the parser encounters decorated AST nodes
- THEN the decorated class is classified as `class`
- AND the decorated function is classified as `function`

### REQ-ABD-002: Unclassifiable Nodes

The system SHALL place any top-level AST node that does not match a known category into `unclassified` and SHALL emit a non-blocking warning to stderr.

#### Scenario: Conditional definition

- GIVEN a Python file where `if TYPE_CHECKING:` wraps a class definition
- WHEN the parser encounters a top-level `If` node containing a `ClassDef`
- THEN the inner `ClassDef` is classified as `unclassified`
- AND a warning is emitted: "unclassified: class inside conditional at line N"

#### Scenario: Module-level expression statement

- GIVEN a file with a bare `print("hello")` at module scope
- WHEN the parser encounters a top-level `Expr` node
- THEN it is classified as `unclassified`
- AND a warning is emitted

### REQ-ABD-003: Module Proposal Generation

The system SHALL produce a module-proposal map keyed by proposed module name, where each value is a list of definition names assigned to that module. The default proposal strategy SHALL group definitions by type (e.g., `models.py` for classes, `functions.py` for functions, `constants.py` for constants).

#### Scenario: Default type-based grouping

- GIVEN a file with classes `A`, `B` and functions `f1`, `f2`
- WHEN the proposal is generated with default strategy
- THEN the map includes `{"models.py": ["A", "B"], "functions.py": ["f1", "f2"]}`

#### Scenario: Empty source file

- GIVEN a Python file containing only comments and no top-level definitions
- WHEN the parser analyzes the file
- THEN the proposal map is empty
- AND a warning is emitted: "no top-level definitions found"

## Cross-Platform Notes

- File reading MUST use `encoding="utf-8"` per AGENTS.md cross-platform rule.
- All path operations MUST use `pathlib.Path` — never string concatenation with `\` or `/`.

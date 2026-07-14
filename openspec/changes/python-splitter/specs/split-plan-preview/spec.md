# split-plan-preview Specification

## Purpose

Render the proposed module tree and a sample diff of the split operation to the user for review BEFORE any file-system writes occur.

## Requirements

### REQ-SPP-001: Module Tree Display

The system SHALL render the proposed module tree as a hierarchical text output using `rich.tree`. The tree MUST show the target package directory, each proposed module file, and the definitions assigned to each module.

#### Scenario: Standard tree display

- GIVEN a proposal that groups classes `User`, `Product` into `models.py` and functions `validate`, `sanitize` into `utils.py`
- WHEN the preview is rendered
- THEN the output shows a tree with the package root, `models.py` listing `User` and `Product`, and `utils.py` listing `validate` and `sanitize`

#### Scenario: Empty proposal

- GIVEN a proposal with no modules (no top-level definitions found)
- WHEN the preview is rendered
- THEN the output states "Nothing to split" and exits with code 0

### REQ-SPP-002: Sample Diff Display

The system SHALL display a sample diff showing one module's expected content after the split to help the user evaluate correctness.

#### Scenario: Diff for first proposed module

- GIVEN a proposal with at least one module
- WHEN the preview is rendered
- THEN a sample diff for the first module is displayed
- AND the diff shows additions only (new file creation)

#### Scenario: Proposal with many modules

- GIVEN a proposal with five or more modules
- WHEN the preview is rendered
- THEN only one sample diff is shown
- AND a note is displayed: "showing diff for {module_name}; {N-1} more modules proposed"

### REQ-SPP-003: User Confirmation Prompt

The system SHALL prompt the user for explicit confirmation before proceeding to split execution. The prompt SHALL default to "no" (dry-run behavior) and SHALL accept a `--yes` / `-y` flag to skip the interactive prompt.

#### Scenario: Interactive prompt — user confirms

- GIVEN a valid proposal is displayed
- WHEN the user responds "yes" at the prompt
- THEN execution proceeds to the split-execution phase

#### Scenario: Interactive prompt — user declines

- GIVEN a valid proposal is displayed
- WHEN the user responds "no" or presses Enter at the prompt
- THEN execution halts and no files are written
- AND the exit code is 0

#### Scenario: Non-interactive flag

- GIVEN the `--yes` / `-y` flag is passed
- WHEN the proposal would be displayed
- THEN no interactive prompt is shown
- AND execution proceeds immediately to split-execution

## Cross-Platform Notes

- Rich handles ANSI fallback on Windows terminals per AGENTS.md — no special handling required at the spec level.

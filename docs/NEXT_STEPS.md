# Development plan

## Current usable milestone

- Version 1: local CLI, SQLite storage, monthly summaries, CSV export, tests.
- Version 1.1: retrieve and display one expense with `show ID`, including missing
  and invalid ID handling, shared output formatting, tests, and documentation.
- Version 1.2: lock category and note length limits with exact boundary tests and
  document a realistic disposable-database workflow.

## Next small milestones

Complete at most one per scheduled development run:

1. Implement an `update` command with explicit field selection, validation, and
   regression tests.
2. Add CSV import with all-or-nothing validation and clear error reporting.
3. Design a FastAPI layer after the learner reaches functions, modules, and
   exceptions through hands-on Python work.
4. Evaluate PostgreSQL and cloud deployment when the API and tests are stable.

Do not label future milestones as completed. Cloud deployment and provider
services need a separate setup decision; this project currently has no hosting
costs. See `DEVELOPMENT_LOG.md` for dated evidence.

# Development plan

## Current usable milestone

- Version 1: local CLI, SQLite storage, monthly summaries, CSV export, tests.
- Version 1.1: retrieve and display one expense with `show ID`, including missing
  and invalid ID handling, shared output formatting, tests, and documentation.
- Version 1.2: lock category and note length limits with exact boundary tests and
  document a realistic disposable-database workflow.
- Version 1.3: update only explicitly selected expense fields, including clearing
  a note, while preserving omitted values and rejecting invalid changes.

## Next small milestones

Complete at most one per scheduled development run:

1. Add CSV import with all-or-nothing validation and clear error reporting.
2. Design a FastAPI layer after the learner reaches functions, modules, and
   exceptions through hands-on Python work.
3. Evaluate PostgreSQL and cloud deployment when the API and tests are stable.

Do not label future milestones as completed. Cloud deployment and provider
services need a separate setup decision; this project currently has no hosting
costs. See `DEVELOPMENT_LOG.md` for dated evidence.

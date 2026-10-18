# Development plan

## Current usable milestone

- Version 1: local CLI, SQLite storage, monthly summaries, CSV export, tests.
- Version 1.1: retrieve and display one expense with `show ID`, including missing
  and invalid ID handling, shared output formatting, tests, and documentation.
- Version 1.2: lock category and note length limits with exact boundary tests and
  document a realistic disposable-database workflow.
- Version 1.3: update only explicitly selected expense fields, including clearing
  a note, while preserving omitted values and rejecting invalid changes.
- Version 1.4: import either the documented four-column CSV format or this app's
  exported five-column format, validate every row before writing, report invalid
  line numbers, and generate fresh local IDs.
- Version 1.4.1: validate deletion IDs before `delete()` opens its query
  connection so booleans, strings, zero, and negative values cannot reach SQL.
- Version 1.4.2: enable strict CSV parsing so broken quoted fields fail with their
  physical line number before the atomic import reaches SQLite.
- Version 1.5: filter `list`, `summary`, and `export` by an exact normalized
  category, independently or together with the existing month filter.

## Next small milestones

Complete at most one per scheduled development run:

1. Keep the usable expense-tracker CLI stable and make only evidence-backed fixes.
2. Continue the separate job-application API after the learner reaches functions,
   modules, and exceptions through hands-on Python work.
3. Evaluate PostgreSQL and cloud deployment when that API and its tests are stable.

Do not label future milestones as completed. Cloud deployment and provider
services need a separate setup decision; this project currently has no hosting
costs. See `DEVELOPMENT_LOG.md` for dated evidence.

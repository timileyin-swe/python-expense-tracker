# Development plan

Version 1: complete local CLI, SQLite storage, monthly summaries, CSV export, tests.

Next small milestones (one per scheduled run):
1. Add real user examples and strengthen edge-case tests based on actual behavior.
2. Implement an update command with validation and regression tests.
3. Add CSV import with atomic validation and clear error reporting.
4. Design a FastAPI layer after the learner reaches functions, modules, and exceptions.
5. Evaluate PostgreSQL and cloud deployment when the API and tests are stable.

Do not label future milestones as completed. Cloud deployment and provider services
need a separate setup decision; this project currently has no hosting costs.

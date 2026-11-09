# Understanding automated testing on GitHub

You already run `python -m unittest discover -s tests -v` locally. Continuous
integration (CI) asks GitHub to run the same check on a fresh computer whenever
code is pushed or a pull request is opened or updated.

## Read the workflow

Open `.github/workflows/tests.yml`:

- `on` lists the events that start the check. `workflow_dispatch` adds a manual
  Run workflow button after this file reaches the default branch.
- `permissions` allows reading repository contents, not modifying them.
- `matrix` creates four jobs: each combination of two operating systems and
  two Python versions. Python 3.10 is the README's minimum supported version;
  3.12 is the version used for the local review. These checks do not prove that
  every newer Python release works.
- `checkout` copies the repository into the runner.
- `setup-python` selects the interpreter. The action's version (such as `v5`)
  is different from the Python version (such as `3.12`).
- `run` executes the existing test suite. No pip installation is needed because
  this project uses only Python's standard library.
- `timeout-minutes` stops a stuck job. `fail-fast: false` lets the other jobs
  finish even when one combination fails.

The tests create temporary databases. They do not need your personal expenses,
passwords, or cloud credentials. A successful check does not deploy anything and
does not automatically prevent a failing branch from being merged; that requires
separate repository rules.

## Practice before adding another feature

1. In `expense_tracker/core.py`, locate `money_to_kobo`. Explain why money is
   stored as integer kobo instead of floating-point naira.
2. Read `test_exact_money` in `tests/test_tracker.py`. Predict its result, then
   run the suite locally.
3. On a disposable practice branch, temporarily change one expected value in
   that test. Run the suite and identify the assertion failure. Restore the
   value and confirm all 34 tests pass again.
4. Explain the difference between a local passing test and a green GitHub check.
5. After publishing the workflow, inspect the Actions tab and find the test
   count and result in each of the four jobs. Do not claim CI passed until you
   have seen those results.

Reference: https://docs.github.com/en/actions/tutorials/build-and-test-code/python

# Agent Skills - TODO

- [ ] **Create an automated test harness (Eval-Driven Development)**: Build a lightweight Python or Bash script (e.g., `scripts/run-evals.sh` or `scripts/run-evals.py`) to automate skill evaluation as outlined in `docs/how-to/evaluating-skills.md`.
  - The script should read `evals/evals.json` from a skill directory.
  - Spin up an isolated sub-agent headlessly (via `pi` or `claude`), pass it the test prompt, and record token usage/duration into `timing.json`.
  - Run an LLM verification step against defined assertions to produce `grading.json` and `benchmark.json`.

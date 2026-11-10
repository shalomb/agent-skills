# Specs

Scenarios in Given/When/Then, one file per area, each tagged with the principle or decision it protects
(see `../docs/INTENT.md`). Each scenario has a stable id (`S-<area>-<n>`). A scenario is "done" when an automated test
names that id in its docstring or test name. Python logic: `unittest` in `../tests/`. Browser behaviour: `../tests/bdd/`
against the synthetic data (no Jira, no network beyond localhost). Run all: `python3 -m unittest discover -s tests`.

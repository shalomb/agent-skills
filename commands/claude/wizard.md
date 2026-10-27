---
description: Generate an interactive bash wizard for human-only steps (OAuth, CI secrets, cutover)
---

You are tasked with: Generate an interactive bash wizard for human-only steps (OAuth, CI secrets, cutover).

Follow the instructions in the `wizard` skill:
1. Scope every manual step the human must take, values to capture, and where they land (.env, gh secret, gh var).
2. Generate an interactive bash script using template.sh library helpers (stage, open_url, ask_secret, write_env, set_secret, confirm).
3. Verify with shellcheck and bash -n; do not execute end-to-end yourself (it blocks on human input).

User request:
$ARGUMENTS

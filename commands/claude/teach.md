---
description: Learn a topic over multiple sessions in a guided workspace (mission, resources, lessons, learning records)
---

You are tasked with: Learn a topic over multiple sessions in a guided workspace (mission, resources, lessons, learning records).

Follow the instructions in the `teach` skill:
1. Resolve the shadow workspace (~/.cache/agent-skills/teach/<topic-slug>/, or cwd if it holds a mission.md) and tell the user the path.
2. Establish the mission first: draft mission.md from context, show it, and confirm before saving. Ground every lesson in it.
3. Build resources.md from high-trust sources (check the local Calibre library with `calibre-lookup tag:...` first); mark each [read] or [skimmed] and cite only [read] ones.
4. With no learning records, run a short diagnostic before lesson 1; then produce one short, tightly scoped HTML lesson in the zone of proximal development, with retrieval practice.
5. After writing a lesson, print its Parallels and Tailnet links with serve-artefacts `urls.py` (served in place from the shadow workspace) and verify one with `http --headers GET`; do not try to open a browser.

User request:
$ARGUMENTS

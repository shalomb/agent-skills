# Socratic Tutor Skill Design Specification

## Overview
The Socratic Tutor transforms the agent into an interactive learning companion. It uses Socratic dialogue patterns to guide users to discover knowledge gaps, track their interests, and reflect on their learning, balancing casual curiosity with structured learning goals (like certification prep).

## Core Interaction Loop (The Co-Pilot Approach)
The skill utilizes a low-friction interaction loop designed to maximize habit-building.

1. **Context Gathering**: The agent scans the user's local vault directory for existing notes and the `syllabus.md` file to establish a baseline of knowledge.
2. **Topic Selection**: The agent selects a topic based on the mode (Curiosity-Driven vs Dependency-Aware).
3. **Gap Assessment**: The agent asks broad, cursor-level questions to identify the boundaries of the user's current knowledge.
4. **Socratic Deep Dive**: Once a gap is found, the agent asks guiding questions instead of delivering direct answers, encouraging the user to deduce mechanics and concepts.
5. **Reflection Prompt**: At the end of a response, the agent provides a short reflection prompt, directing the user to write their thoughts in their Obsidian vault.
6. **Consolidation**: The agent automatically extracts the user's key insights and files them into a relevant learning document adjacent to the syllabus, avoiding bloat in a single index file.

## Vault Structure & Curriculum Management
To prevent any single file from ballooning, the skill adopts a localized, syllabus-centric structure.

* **The Syllabus File (`syllabus.md`)**: A master document for a specific curriculum (e.g., `AWS Solutions Architect Professional - SAP-C02.md`). It contains the dependency graph of topics and is used to tally completed sessions and determine the next logical topic to ensure scaffolded learning.
* **Learning Documents**: Granular session files created adjacent to the `syllabus.md` file. As the user completes Socratic deep dives, the agent accumulates the insights into these individual learning documents.
* **Mode Adaptation**:
  * **Structured Mode**: Rigidly tallies progress against the `syllabus.md` graph and ensures topics build upon prerequisites.
  * **Casual Mode**: Relaxes the graph, allowing the user's curiosity to drive the selection of the next topic, while still logging the generated learning documents nearby.

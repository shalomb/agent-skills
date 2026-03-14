---
name: copilot-cli
description: Execute GitHub Copilot CLI commands programmatically for AI-powered code generation, analysis, and automated coding tasks. Supports non-interactive mode, autopilot, permission controls, session management, and output capture for CI/CD integration. Trigger when the user mentions copilot, gh copilot, or AI-powered code generation/refactoring.
---

# GitHub Copilot CLI Skill

This skill provides programmatic execution of GitHub Copilot CLI commands for code generation, analysis, and automation tasks.

## Prerequisites

- GitHub Copilot CLI installed (`copilot --version`)
- Authenticated with GitHub (`copilot login`)
- Valid Copilot subscription

## Usage Instructions

The GitHub Copilot CLI supports complex non-interactive workflows and autopilot continuation. **DO NOT GUESS THE CLI FLAGS.**

1. Whenever you need to use the Copilot CLI (e.g. for generating shell scripts, refactoring code, analyzing bugs, or managing sessions), you must first read the detailed reference documentation to see the exact flags and usage patterns:
   - Use the `read` tool to load `references/copilot-cli-reference.md`.
   
2. The reference file contains instructions for:
   - Running in non-interactive prompt mode
   - Using autopilot for multi-step tasks
   - Permission controls and execution safety
   - Managing and sharing Copilot sessions
   - Output capture for automation and CI/CD

3. Always follow the documented patterns for executing commands to avoid interactive prompts hanging the agent's execution loop.

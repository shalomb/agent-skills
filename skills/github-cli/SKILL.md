---
name: github-cli
description: Execute GitHub CLI (gh) commands for repository management, issues, pull requests, workflows, releases, and API interactions (REST & GraphQL). Use when working with GitHub repositories, managing issues and PRs, executing workflows, or querying the GitHub API.
---

# GitHub CLI (gh) Skill

This skill provides comprehensive GitHub CLI integration for managing repositories, issues, pull requests, workflows, releases, and API interactions (both REST and GraphQL).

## Prerequisites

- GitHub CLI (`gh`) must be installed and authenticated
- `gh auth login` successfully completed
- Active internet connection for GitHub API access
- Appropriate repository permissions for target operations

## Usage Instructions

This skill has a broad command surface and supports powerful API interactions. **DO NOT GUESS COMMAND FLAGS OR GRAPHQL QUERIES.**

1. Whenever you need to perform complex operations with the GitHub CLI (e.g. advanced PR management, workflows, or raw API calls), you must first read the detailed reference documentation to see the exact syntax:
   - Use the `read` tool to load `references/github-cli-reference.md`.
   
2. The reference files contain instructions for:
   - Repository, Issue, and Pull Request operations
   - Advanced PR operations: marking as draft, adding comments with context
   - GitHub Actions workflow triggering and monitoring
   - Advanced REST API calls via `gh api`
   - Complex GraphQL queries and mutations via `gh api graphql`
   - **Issue Hierarchy (Parent/Child)**: See `references/issue-hierarchy.guide.md`
   - **Team Management Operations**: See `references/github-team-management.md`
   - **PI Epic Issues**: See `references/epic-issue-template.md` — template, labels, body structure, and the safe issue-rewrite pattern
   - Common developer workflow examples

3. **Team Management Best Practices**:
   - Always verify user has admin/maintain permissions before adding teams to repositories
   - Handle repository redirects (renamed repos) gracefully
   - Test operations on a single repository before bulk operations
   - Use appropriate permission levels (prefer `push` for most teams)

4. Whenever possible, use built-in `gh` commands rather than writing raw `curl` commands or custom Python scripts for GitHub integration.

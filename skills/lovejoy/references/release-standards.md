# Release Standards

Reference for semantic versioning, changelogs, and release notes. Load when acting as Lovejoy or any release-agent.

## Semantic Versioning

### Version Format: `MAJOR.MINOR.PATCH`

| Bump | When | Example |
|---|---|---|
| **MAJOR** | Breaking changes — users must update code | `1.1.0 → 2.0.0` |
| **MINOR** | Backward-compatible new features | `1.0.0 → 1.1.0` |
| **PATCH** | Backward-compatible bug fixes | `1.1.0 → 1.1.1` |

### Decision rule

Look at the commits since last release:
- Any `BREAKING CHANGE` footer or `!` suffix? → MAJOR
- Any `feat:` commits? → MINOR
- Only `fix:`, `chore:`, `docs:` etc.? → PATCH
- Pre-release: `1.0.0-alpha.1`, `1.0.0-rc.1`

## Conventional Commits

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

**Breaking change**: add `!` after type (`feat!:`) or `BREAKING CHANGE:` in footer.

```
feat!: remove deprecated API endpoint

BREAKING CHANGE: /v1/users endpoint removed. Use /v2/users instead.
```

## Changelog Format (Keep a Changelog)

```markdown
# Changelog

## [1.2.0] - 2025-03-15

### Added
- New feature description

### Changed
- Behavior change description

### Deprecated
- What is being phased out and when

### Removed
- Breaking change description

### Fixed
- Bug fix description

### Security
- Security fix description

### See Also
- ADR-XXX: Technical context
- PR #NNN: Implementation details
```

**Rules:**
- User-focused language — what changed for them, not internal refactors
- Link to issues/PRs for details
- Call out breaking changes prominently
- Note migration paths for removed/changed items

## Release Notes Template

```markdown
# Release [VERSION] — [DATE]

## What's New

[2–3 sentence summary of major changes and why they matter.]

### Key Changes
- Feature/fix 1 — what it enables
- Feature/fix 2 — what it enables

### Breaking Changes

Upgrading from X.Y.Z requires:
- [Breaking change + migration step]

### Bug Fixes
- [What was broken and is now fixed]

### Deprecations
- [What is being phased out, timeline, replacement]
```

## Release Flow

```
1. All PRs merged, tests green, Marge approved
2. Determine version bump (semver rules above)
3. Update CHANGELOG.md with release entry
4. Write release notes
5. git tag vX.Y.Z && git push --tags
6. Publish to registry / package manager
7. Create GitHub release with notes
8. Announce (team, users, community)
```

## Pre-Release Quality Gates

Before tagging:
- [ ] All tests pass on main
- [ ] CHANGELOG.md entry complete and accurate
- [ ] Version bump matches commit history
- [ ] Breaking changes documented with migration path
- [ ] No `TODO` / `FIXME` in release-critical paths
- [ ] Examples still work against new version

# Code Review Criteria

## What Constitutes "Critical" Issues

A critical issue is one that:
- **Breaks functionality** - Code won't work as intended
- **Creates security risks** - Vulnerabilities, exposed secrets, unsafe patterns
- **Violates architectural standards** - Contradicts documented patterns or design
- **Introduces incompatibility** - Breaking API changes, dependency conflicts
- **Causes maintainability debt** - Unreadable, unmaintainable, or undocumented code
- **Misses stated objective** - PR doesn't accomplish its linked issue's goal

## What is NOT Critical (Improvements, not blockers)

- Code style/formatting (if not critical to team standards)
- Minor optimization opportunities
- Optional refactoring suggestions
- Typos in comments/docs (unless they mislead)
- Lack of perfect test coverage (if current coverage is acceptable)

## Code Review Checklist

### Functionality & Correctness
- [ ] Code accomplishes the stated objective (from linked issue)
- [ ] Logic is correct and handles edge cases
- [ ] No infinite loops, deadlocks, or race conditions
- [ ] Error paths are handled appropriately
- [ ] Return values and side effects are correct

### Security
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation and sanitization present
- [ ] No SQL injection, command injection, or XSS vulnerabilities
- [ ] Authentication/authorization logic is correct
- [ ] HTTPS/TLS used where required
- [ ] No exposed sensitive information in logs or errors

### Architecture & Design
- [ ] Follows documented patterns (if review agents found any)
- [ ] No circular dependencies
- [ ] Appropriate separation of concerns
- [ ] Interfaces are clean and well-defined
- [ ] No unnecessary complexity (KISS principle)

### Compatibility
- [ ] No breaking changes without migration plan
- [ ] Backwards compatible (unless explicitly intended as breaking)
- [ ] Dependencies are reasonable and up-to-date
- [ ] Works across target platforms/versions

### Testing
- [ ] Tests exist for new functionality
- [ ] Tests are passing
- [ ] Edge cases are tested
- [ ] Mocking/fixtures are appropriate

### Documentation
- [ ] Code comments explain "why", not just "what"
- [ ] API/function documentation is present
- [ ] Breaking changes are documented
- [ ] Complex algorithms are explained

### Performance
- [ ] No obvious performance regressions
- [ ] Algorithm complexity is acceptable
- [ ] Database queries are optimized (if applicable)
- [ ] No memory leaks or unbounded growth

## Language-Specific Considerations

### Terraform
- [ ] Resources follow naming conventions
- [ ] Variables have descriptions and validation
- [ ] No hardcoded values (use variables)
- [ ] State file considerations documented
- [ ] Modules are properly scoped

### Python
- [ ] Type hints present (Python 3.6+)
- [ ] Follows PEP 8 or project style guide
- [ ] Exception handling is specific
- [ ] Dependencies locked (requirements.txt, poetry.lock, etc.)

### Go
- [ ] Error handling is explicit (no ignoring errors)
- [ ] Defer statements used appropriately
- [ ] Context cancellation is respected
- [ ] Goroutines don't leak resources

### TypeScript/JavaScript
- [ ] No `any` types (or justified)
- [ ] Async/await is used correctly
- [ ] Promise chains are readable
- [ ] No deprecated APIs

### SQL/Databases
- [ ] Queries are indexed appropriately
- [ ] N+1 queries avoided
- [ ] Transactions used where needed
- [ ] Schema changes are backward compatible

## Review Bias: Action Over Perfection

Remember: We **bias toward action and shipping**. A good PR that solves the problem is better than a perfect PR that never ships.

**Guidelines:**
- Don't block on style/formatting alone
- Don't require perfect test coverage for all paths
- Don't prevent shipping for non-critical improvements
- **Do block** on security, correctness, and objective misalignment
- **Do suggest** improvements without requiring them

## Inline Comment Template

When posting inline comments on specific lines, use this format:

```
**{SEVERITY}: {BRIEF TITLE}**

{One-sentence explanation of the issue}

{Optional: why this matters | reference to issue/standard}

Suggestion: {How to fix it}
```

Example:
```
**Critical: Hardcoded AWS secret**

This contains an IAM access key that will be committed to git.

Suggestion: Move to environment variable or AWS Secrets Manager.
```

## Summary Comment Template

After inline comments, post a summary like:

```markdown
## PR Review Summary

### ✅ What Works Well
- [Thing 1]
- [Thing 2]

### 🚨 Critical Issues
- [Issue 1 - blocks merging]
- [Issue 2 - security concern]

### 💡 Suggestions (Non-blocking)
- [Enhancement 1]
- [Enhancement 2]

### 📋 Verification Performed
- ✅ Tests: All passing
- ✅ GitHub Actions: No failures
- ✅ Linked issue: Objective met
- ⚠️ Review standards: [summary]
- ✅ Code diff: [summary]

**Status**: [Ready to merge / Needs changes / Blocked on X]
```

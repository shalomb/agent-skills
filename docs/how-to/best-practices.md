# How-to: Skill Best Practices

This guide covers best practices for creating high-quality, maintainable skills.

## 1. Writing Effective Descriptions

Your skill's description is critical - it determines when Claude auto-invokes it.

### ❌ Poor Descriptions

```yaml
description: Does code stuff
description: Useful helper
description: Code generation
```

### ✅ Good Descriptions

```yaml
description: Generates unit tests for Python functions using pytest. Analyzes function signatures and behavior to create comprehensive test cases with >80% coverage.
description: Reviews code for security vulnerabilities including injection attacks, authentication issues, and data validation problems.
description: Refactors code for readability, performance, and maintainability. Suggests specific improvements with explanations.
```

### Description Best Practices

1. **Be Specific**: Include the tool (pytest, pytest) and outcome (>80% coverage)
2. **Include Keywords**: Use terms Claude will match ("unit tests", "security review")
3. **Mention When to Use**: "When testing Python functions", "Before code review"
4. **Action-Oriented**: Start with what the skill does
5. **One Skill, One Purpose**: Don't try to do too much

**Template:**

```yaml
description: {Action} for {domain} {artifacts}. Use when {trigger}. {Details about approach or requirements}.
```

**Examples using the template:**

```yaml
description: Generates unit tests for Python functions using pytest. Use when implementing new functions or improving coverage. Analyzes signatures and creates tests with >80% coverage.

description: Identifies security vulnerabilities in code including injection attacks, auth issues, and data validation. Use before merging to main or deploying to production. 

description: Refactors code for performance, readability, and maintainability. Use when code is slow, hard to understand, or violates style guide. Provides specific suggestions with explanations.
```

## 2. Structuring Skill Content

Organize your skill instructions clearly.

### ✅ Good Structure

```yaml
---
name: test-generator
description: Generates unit tests for Python code with >80% coverage using pytest
---

## Overview

This skill generates comprehensive unit tests for Python functions.

## Process

When invoked, I will:

1. Analyze the function's purpose, inputs, and behavior
2. Identify edge cases and error conditions
3. Generate test cases with clear assertions
4. Ensure >80% code coverage
5. Follow pytest conventions

## Guidelines

### Test Coverage

- Normal operation (happy path)
- Edge cases (empty inputs, None, etc.)
- Error conditions (invalid types, exceptions)
- Boundary conditions

### Code Style

- Use descriptive test names: `test_function_with_valid_input`
- Use `@pytest.mark` for categorizing tests
- Include docstrings explaining test intent

### Assertions

- One assertion per test (when possible)
- Use `pytest.approx()` for floating point comparisons
- Use context managers for exception testing

## Example Output

See `examples/generated_tests.py` for a full example.
```

### Structure Template

```yaml
---
name: {skill-name}
description: {clear description}
---

## Overview
Brief explanation of what the skill does.

## Process
Step-by-step what Claude will do.

## Guidelines
Rules Claude should follow.

## Example
Example output or reference.
```

## 3. Handling User Input and Arguments

Skills should handle arguments gracefully.

### Accepting Arguments

```yaml
---
name: language-converter
description: Converts code from one programming language to another
---

## Usage

Invoke with: `/language-converter Convert this to Python`

The target language is specified in your request.

## Process

1. Detect the source language from the code
2. Parse the code structure and logic
3. Convert to target language with idiiomatic patterns
4. Verify logical equivalence
5. Review for performance implications
```

### Validating Arguments

```yaml
---
name: test-generator
description: Generates tests for Python code
---

## Handling Arguments

If you specify test types with `/test-generator unit`, I will:
- Check if the type is valid: unit, integration, e2e
- Use appropriate test framework (pytest for Python)
- Apply type-specific patterns

If no type specified, I generate comprehensive unit tests.
```

## 4. Error Handling and Troubleshooting

Include guidance for common issues.

```yaml
---
name: database-migrator
description: Generates database migration files
---

## Troubleshooting

### No database detected
If I can't detect your database:
- Check DATABASE_URL is set in .env
- Verify database connection string is valid
- Confirm I have read access to schema

### Migration too large
If generated migration is >500 lines:
- Break it into smaller migrations
- Migrate data and schema separately
- Test each migration independently

### Rollback issues
If a migration fails:
- Provide rollback logic to undo changes
- Ensure data consistency
- Test rollback before applying
```

## 5. Clear and Concise Instructions

Claude works better with clear, specific instructions.

### ❌ Vague Instructions

```yaml
---
name: refactor
description: Makes code better
---

Refactor the code for improvement.
```

### ✅ Clear Instructions

```yaml
---
name: refactor-performance
description: Refactors code for performance improvements with specific optimizations
---

## Performance Optimization Process

1. **Profile**: Identify performance bottlenecks
   - Look for nested loops and O(n²) operations
   - Check for redundant computations
   - Identify memory-intensive operations

2. **Optimize**: Apply specific improvements
   - Replace nested loops with vectorization
   - Cache repeated computations
   - Use efficient data structures (set vs list lookup)
   - Reduce memory allocations

3. **Measure**: Verify improvements
   - Run benchmarks before and after
   - Compare execution time
   - Check memory usage

4. **Document**: Explain changes
   - Why the optimization matters
   - Performance improvement (%)
   - Any trade-offs (readability, maintainability)

## Example Optimizations

- `n²` algorithm → `O(n log n)` with sorting
- Repeated lookups → Cached dictionary
- String concatenation → f-strings
- List comprehension → Generator expressions for large data
```

## 6. Testing Your Skills

Before sharing, test thoroughly.

### Test Checklist

- [ ] Skill directory structure is correct
- [ ] `SKILL.md` has proper YAML frontmatter
- [ ] Description accurately describes the skill
- [ ] Direct invocation works (`/skill-name`)
- [ ] Auto-invocation triggers on matching requests
- [ ] Instructions are clear and specific
- [ ] Examples (if provided) are correct
- [ ] Supporting files are referenced correctly
- [ ] No broken links or references
- [ ] Works across different project types

### Testing Commands

```bash
# Verify skill structure
ls -la ~/.claude/skills/my-skill/

# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('SKILL.md'))"

# Test direct invocation
/my-skill test input

# Test auto-invocation
Ask a question matching the skill description
```

## 7. Naming Conventions

Use consistent naming for skills.

### ✅ Good Names

- `explain-code` - Explains code
- `test-generator` - Generates tests
- `refactor-performance` - Refactors for performance
- `security-reviewer` - Reviews security

### ❌ Avoid

- `util` - Too generic
- `my-awesome-skill` - "awesome" is subjective
- `do-stuff` - Unclear purpose
- `helper` - Doesn't describe function

### Naming Pattern

```
{action}-{domain}
{action}-{target}
{tool}-{type}
```

Examples:
- `generate-tests`, `generate-docs`
- `refactor-performance`, `refactor-readability`
- `review-security`, `review-code-quality`
- `pytest-helper`, `docker-assistant`

## 8. Documentation and Examples

Include examples in your skills.

### Add Examples Directory

```
~/.claude/skills/test-generator/
├── SKILL.md
└── examples/
    ├── simple_function_test.py
    ├── async_function_test.py
    └── class_method_test.py
```

### Reference Examples

```yaml
---
name: test-generator
description: Generates unit tests for Python code with >80% coverage
---

## Examples

For examples of generated tests, see the `examples/` directory:
- `simple_function_test.py` - Basic function testing
- `async_function_test.py` - Async/await testing
- `class_method_test.py` - Class and method testing
```

## 9. Version and Dependency Management

Document requirements clearly.

```yaml
---
name: python-tester
description: Generates unit tests for Python code
requires: python>=3.8
tags:
  - testing
  - python
notes: "Requires pytest. Install with: pip install pytest>=6.0"
---
```

## 10. Regular Maintenance

Keep skills updated and relevant.

### Maintenance Checklist

- [ ] Does the skill still work with current tool versions?
- [ ] Are dependencies up to date?
- [ ] Is the description still accurate?
- [ ] Have you received feedback to incorporate?
- [ ] Should supporting files be updated?
- [ ] Are examples still relevant?

### Version Your Skills

Include version info in notes:

```yaml
---
name: react-helper
notes: "Updated for React 18. Previous versions: https://..."
---
```

## Example: Well-Maintained Skill

Here's a complete example following all best practices:

```yaml
---
name: api-test-generator
description: Generates comprehensive API tests for REST endpoints using pytest. Covers happy paths, error cases, and edge cases. Use when implementing new APIs or improving test coverage.
invocation_type: autonomous
requires: python>=3.8
tags:
  - testing
  - api
  - pytest
access_level: user
notes: "v1.2 - Updated for pytest 7.0. Supports async endpoints."
---

## API Test Generation

Generate comprehensive tests for REST API endpoints.

## Process

1. Analyze endpoint specification
2. Identify test cases (happy path, errors, edge cases)
3. Generate test code with proper assertions
4. Include setup/teardown and fixtures
5. Ensure >80% coverage

## Guidelines

### Test Organization

- Group by endpoint
- Use fixtures for shared setup
- Mock external dependencies

### Assertions

- Status codes correct
- Response schema valid
- Error messages helpful
- Performance acceptable

### Examples

See `examples/` directory for generated test examples.

## Troubleshooting

**Missing endpoints?**
- Provide full endpoint specifications
- Include request/response examples

**Tests not running?**
- Check Python version >= 3.8
- Verify pytest installed: `pip install pytest`
- Run tests: `pytest test_api.py`
```

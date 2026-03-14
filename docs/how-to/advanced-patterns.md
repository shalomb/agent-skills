# How-to: Advanced Skill Patterns

This guide covers advanced patterns for creating powerful, flexible skills.

## Pattern 1: Inject Dynamic Context

Inject dynamic context from your project into Claude when the skill is invoked.

### Basic Example

Create a skill that has access to project-specific information:

```yaml
---
name: project-analyzer
description: Analyzes your project structure and provides recommendations
---

## Project Context

Your project contains:
- Frontend: {frontend_framework}
- Backend: {backend_language}
- Database: {database_type}
- Node version: {node_version}

Based on this context, provide recommendations for:
1. Performance optimization
2. Security improvements
3. Scalability patterns
```

### Getting Context Information

Extract dynamic context by reading project files:

```yaml
---
name: framework-guide
description: Provides framework-specific guidance
---

## Detected Framework

From package.json, this project uses:
- {framework_version}

Refer to framework-specific best practices below.

[Read framework from package.json contents]
```

### Practical Example: Database Advisor

```yaml
---
name: database-advisor
description: Provides database optimization advice specific to your project
---

## Database Configuration

Current database: {database_type}
Version: {database_version}

### Optimization Recommendations

For {database_type}, consider:

1. Index strategy - See recommendations below
2. Query optimization patterns
3. Connection pooling settings

[Provide database-specific advice]
```

## Pattern 2: Run Skills in a Subagent

Create a skill that delegates to a specialized subagent for focused work.

### Basic Subagent Skill

```yaml
---
name: code-review-team
description: Spawns a team of specialized review agents to review code
---

## Code Review Process

I will spawn three specialized review agents:

1. **Performance Reviewer**: Checks for performance bottlenecks
2. **Security Reviewer**: Identifies security vulnerabilities
3. **Quality Reviewer**: Ensures code quality and maintainability

Each agent will:
- Analyze the provided code
- Generate a detailed report
- Suggest specific fixes

[Let agents work in parallel]
[Aggregate findings]
[Present consolidated report]
```

### Subagent Pattern Example: Batch Changes

```yaml
---
name: batch-refactor
description: Coordinates large refactoring across your codebase using multiple agents
---

## Batch Refactoring Coordinator

This skill will:

1. **Analyze** the request and affected files
2. **Plan** the refactoring strategy
3. **Decompose** into independent units (5-30 tasks)
4. **Present** plan for approval
5. **Execute** with one agent per unit in parallel
6. **Create** pull requests from each agent

This allows coordinated, parallel refactoring while maintaining quality.
```

## Pattern 3: Structured Output with Context

Combine dynamic context injection with structured outputs:

```yaml
---
name: project-report
description: Generates structured project health reports
---

## Project Health Report

**Project**: {project_name}
**Language**: {primary_language}
**Type**: {project_type}

### Code Metrics

Based on the repository:
- Files analyzed: {file_count}
- Languages detected: {languages}
- Test coverage: {test_coverage}

### Recommendations

Provide 3-5 prioritized recommendations for:
1. Performance
2. Testing
3. Documentation
4. Security
5. Maintainability
```

## Pattern 4: Multi-Step Skill Workflows

Create skills that guide users through complex workflows:

```yaml
---
name: feature-workflow
description: Guides development of a new feature end-to-end
invocation_type: explicit
---

## Feature Development Workflow

Follow these steps to implement a new feature:

### Step 1: Requirements Analysis
- Clarify feature scope
- Identify dependencies
- Plan data model changes

### Step 2: Implementation
- Create feature branch
- Implement core functionality
- Add error handling

### Step 3: Testing
- Write unit tests
- Add integration tests
- Test edge cases

### Step 4: Review & Merge
- Prepare for code review
- Address feedback
- Merge to main

At each step, I will guide you and check your progress.
```

## Pattern 5: Conditional Logic in Skills

Use markdown and natural language to implement conditional behavior:

```yaml
---
name: smart-formatter
description: Formats code according to its type
---

## Smart Code Formatter

I will analyze your code and apply appropriate formatting.

**If JavaScript/TypeScript:**
- Use Prettier configuration from package.json
- Enforce 2-space indentation
- Use semicolons

**If Python:**
- Use Black formatter style
- Follow PEP 8 guidelines
- Enforce snake_case naming

**If Go:**
- Use gofmt standards
- Enforce interface{} patterns
- Check error handling

I'll detect the language and apply the correct rules.
```

## Pattern 6: Skill with Supporting Templates

Organize skills with reusable templates:

Directory structure:

```
~/.claude/skills/doc-generator/
├── SKILL.md
├── templates/
│   ├── api-docs.md.template
│   ├── getting-started.md.template
│   └── troubleshooting.md.template
└── examples/
    ├── example-api.md
    └── example-getting-started.md
```

**SKILL.md:**

```yaml
---
name: doc-generator
description: Generates project documentation from templates
---

## Documentation Generator

I will create:

1. **API Documentation** - Using `templates/api-docs.md.template`
2. **Getting Started** - Using `templates/getting-started.md.template`
3. **Troubleshooting** - Using `templates/troubleshooting.md.template`

See `examples/` for sample generated documentation.

### Your Documentation

Based on your code, I'll fill in:
- Function signatures and descriptions
- Installation instructions
- Common issues and solutions
```

## Pattern 7: Cascading Skills

Create skills that build on each other:

```yaml
---
name: refactor-then-test
description: Refactors code and automatically generates tests for the refactored code
---

## Refactor and Test Workflow

### Phase 1: Refactoring
I will refactor your code for clarity and maintainability.

### Phase 2: Test Generation
After refactoring, I will:
- Analyze the refactored code
- Generate comprehensive test cases
- Ensure 80%+ coverage

This ensures refactored code is well-tested.
```

## Best Practices for Advanced Patterns

1. **Clear Workflow**: Break complex tasks into clear, sequential steps
2. **Feedback Points**: Ask for approval or confirmation at key steps
3. **Documentation**: Explain what each phase does and why
4. **Error Handling**: Include guidance on handling errors and edge cases
5. **Examples**: Provide example outputs when possible
6. **Context Awareness**: Use dynamic context to make skills project-specific
7. **Subagent Coordination**: When using subagents, clearly describe the division of work

## Examples Repository

Common advanced patterns are available in the examples directory:

- `example-research-skill/`: Uses Explore subagent for research
- `example-batch-skill/`: Coordinated parallel refactoring
- `example-workflow-skill/`: Multi-step feature development
- `example-template-skill/`: Template-based code generation

See each example's README for implementation details.

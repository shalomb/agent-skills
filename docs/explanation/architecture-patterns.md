# Architecture Patterns: Three Skill Categories

At Anthropic, early skill creators fell into three patterns. Understanding which pattern fits your use case helps you structure instructions effectively.

## Pattern 1: Document & Asset Creation

**Purpose**: Create consistent, high-quality output (documents, designs, code, presentations)

**When to use**:
- You have a style guide, template, or standard format
- Users need polished output ready for distribution
- Quality consistency matters more than customization
- Example: "Create a frontend design" → Must follow brand guidelines

**Key Characteristics**:
- Uses Claude's built-in capabilities (artifacts, code execution)
- Doesn't require MCP servers (but can enhance them)
- Focused on output quality and consistency
- Often includes review/approval gates

### Example: Frontend Design Skill

```markdown
---
name: frontend-design
description: Creates distinctive, production-grade frontend interfaces. Use when building web components, pages, apps, or designs.
---

# Frontend Design Skill

## Instructions

### Step 1: Understand Requirements
Ask the user for:
- Page/component type (form, dashboard, card, etc.)
- Purpose and context
- Any existing brand guidelines

### Step 2: Generate Design
1. Reference brand style guide (references/brand-guide.md)
2. Create accessible HTML/CSS
3. Ensure responsive design
4. Use embedded templates

### Step 3: Quality Check
- Color contrast passes WCAG AA
- Mobile responsive (tested at 375px width)
- Loads in < 1 second
- No accessibility violations

### Step 4: Deliver
Create a live preview artifact with:
- Clean, production-ready code
- Comments explaining choices
- Links to design system components
```

**Structure**:
```
frontend-design/
├── SKILL.md (instructions + templates)
├── scripts/ (optional: validation, optimization)
└── references/
    ├── brand-guide.md
    ├── color-palette.md
    ├── typography-guide.md
    └── templates/ (HTML/CSS templates)
```

**Real-World Examples**:
- **docx skill**: Creates Word documents with consistent formatting
- **pptx skill**: Generates presentations from outlines
- **frontend-design skill**: Builds responsive web components
- **code-generator skill**: Scaffolds project structure

---

## Pattern 2: Workflow Automation

**Purpose**: Orchestrate multi-step processes across multiple services

**When to use**:
- Users have a standard workflow they repeat
- Process has clear steps and dependencies
- Requires calling multiple MCP servers
- Example: "Onboard this customer" → Account → Payment → Email

**Key Characteristics**:
- Calls multiple MCP servers in sequence
- Validates at each step before proceeding
- Includes rollback/error handling
- Embeds domain knowledge (e.g., "always check payment first")

### Example: Customer Onboarding Skill

```markdown
---
name: customer-onboarding
description: Manages complete customer onboarding. Use when user says "onboard new customer", "set up subscription", or "create account".
---

# Customer Onboarding Skill

## Workflow

### Phase 1: Account Setup
1. Collect required info:
   - Company name
   - Primary contact email
   - Plan type
2. Call MCP: `create_account`
3. Validate: Account ID received
4. Store account ID for later steps

### Phase 2: Payment Setup
1. Call MCP: `setup_payment_method`
   Parameters: account_id, payment_type
2. Verify: Payment method confirmed
3. On failure: Offer alternative payment methods

### Phase 3: Create Subscription
1. Call MCP: `create_subscription`
   Parameters: account_id, plan_id, payment_method_id
2. Verify: Subscription active
3. Generate invoice

### Phase 4: Send Welcome
1. Call MCP: `send_email`
   Template: welcome_email.md
   Recipients: [customer_email]
2. Log: Email sent confirmation

## Error Handling

### Account Creation Failed
- Cause: Email already exists
- Fix: Check existing account vs. create new
- User decision: Use existing or different email

### Payment Failed
- Cause: Invalid card
- Fix: Ask for different payment method
- Retry: Up to 2 times

### Subscription Failed
- Cause: Feature not available in plan
- Fix: Recommend paid plan upgrade
- Decision: User chooses plan or cancels
```

**Structure**:
```
customer-onboarding/
├── SKILL.md (workflow steps + MCP calls)
├── scripts/
│   └── validate_account.py (validation logic)
└── references/
    ├── error-scenarios.md
    ├── templates/
    │   └── welcome_email.md
    └── mcp-endpoints.md
```

**Real-World Examples**:
- **skill-creator skill**: Guide users through skill creation
- **customer-onboarding skill**: Multi-step account setup
- **project-setup skill**: Initialize templates and permissions
- **github-issue-automation skill**: Triage and assign issues

---

## Pattern 3: MCP Enhancement (Knowledge Layer)

**Purpose**: Add expertise and best practices on top of existing MCP server access

**When to use**:
- You already have an MCP server working
- Users need guidance on "how to use it well"
- Want to embed domain knowledge
- Example: "Analyze this error in Sentry" → Uses Sentry MCP + skill knowledge

**Key Characteristics**:
- Assumes MCP server already works
- Focuses on methodology, not tool access
- Embeds best practices and domain expertise
- Coordinates multiple tool calls intelligently

### Example: Sentry Code Review Skill

```markdown
---
name: sentry-code-review
description: Analyzes GitHub PRs using Sentry error monitoring data. Use when reviewing code or analyzing production bugs.
---

# Sentry Code Review Skill

## Workflow

### Phase 1: Gather Context
1. Get GitHub PR details via MCP
2. Fetch related Sentry errors via MCP
3. Identify affected services

### Phase 2: Analyze with Domain Knowledge
1. Check: "Is error recent or long-standing?"
   - Recent (< 1 week): Likely caused by recent change
   - Long-standing: Might be infrastructure issue
2. Check: "Error rate trend?"
   - Increasing: Regression
   - Stable: Known issue
3. Assess: Impact level

### Phase 3: Code Review
1. Identify touched files in PR
2. Cross-reference with affected code in Sentry
3. Highlight risky changes

### Phase 4: Recommendations
Suggest fixes based on:
- Error patterns in Sentry
- Related errors in same codebase
- Known solutions for this error type
```

**Structure**:
```
sentry-code-review/
├── SKILL.md (methodology + expertise)
├── scripts/
│   ├── error_analyzer.py (domain logic)
│   └── risk_assessor.py (risk scoring)
└── references/
    ├── error-patterns.md
    ├── common-fixes.md
    └── risk-framework.md
```

**Real-World Examples**:
- **sentry-code-review skill**: Error analysis expertise
- **compliance-checker skill**: Governance knowledge on top of MCP
- **data-quality skill**: Statistical analysis expertise
- **accessibility-checker skill**: WCAG expertise layer

---

## Comparison Table

| Aspect | Document Creation | Workflow Automation | MCP Enhancement |
|--------|------------------|-------------------|-----------------|
| **Primary use** | Polished output | Multi-step processes | Expertise layer |
| **MCP required** | Optional | Yes (usually) | Yes |
| **Dependencies** | Templates | Multiple MCP servers | Domain knowledge |
| **Focus** | Quality & consistency | Steps & validation | Best practices |
| **Error handling** | Validation gates | Step-by-step recovery | Context-aware fixes |
| **Example** | Design system skill | Customer onboarding | Sentry analyzer |

---

## Choosing Your Pattern

### You should build a **Document Creation** skill if:
- ✅ Output format matters (style, brand, structure)
- ✅ Users need ready-to-use results
- ✅ Consistency is critical
- ✅ Few external dependencies
- ❌ NOT heavy workflow orchestration

### You should build a **Workflow Automation** skill if:
- ✅ Users repeat multi-step processes
- ✅ Requires calling multiple services
- ✅ Order of steps matters
- ✅ Validation at each step is important
- ❌ NOT just static output generation

### You should build a **MCP Enhancement** skill if:
- ✅ You already have working MCP server(s)
- ✅ Users need methodology guidance
- ✅ Domain expertise improves tool usage
- ✅ Coordinating multiple tool calls
- ❌ NOT creating standalone workflows

---

## Hybrid Skills (Multiple Patterns)

Some skills combine patterns:

**Example**: Document + Workflow
```markdown
name: project-proposal-automation
description: Creates project proposals and sets up tracking in Linear.

# Pattern 1: Document (create proposal)
1. Gather requirements
2. Generate proposal document
3. Get approval

# Pattern 2: Workflow (setup in Linear)
1. Create Linear project
2. Link to proposal
3. Create initial tasks
```

**Example**: Workflow + MCP Enhancement
```markdown
name: deployment-automation
description: Deploys to cloud and monitors health.

# Pattern 2: Workflow (deployment steps)
1. Build application
2. Upload to cloud
3. Run tests

# Pattern 3: Enhancement (monitoring expertise)
1. Configure monitoring dashboards
2. Set up alerts based on best practices
3. Provide runbook for common issues
```

---

## Next Steps

Once you've identified your pattern:
1. Read [How to Create Your First Skill](../how-to/create-first-skill.md)
2. Follow the structure template for your pattern
3. See pattern examples in [Skills on GitHub](https://github.com/topics/agent-skills)

---

**Related**: [Use case design](./use-case-design.md) | [MCP + Skills](./mcp-plus-skills.md)

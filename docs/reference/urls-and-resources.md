# URLs and Resources Reference

Complete list of external URLs, APIs, and references used throughout this documentation system. Use this as a lookup when referencing external resources or navigating to related materials.

## Official Agent Skills Documentation

| Resource | URL | Purpose |
|----------|-----|---------|
| **Agent Skills Home** | https://agentskills.io | Main documentation site |
| **Agent Skills Specification** | https://agentskills.io/specification | Complete SKILL.md format and constraints |
| **Agent Skills Overview** | https://agentskills.io/what-are-skills | What skills are and how they work |
| **Adding Skills Support** | https://agentskills.io/client-implementation/adding-skills-support | Guide for agent/IDE developers |
| **Optimizing Descriptions** | https://agentskills.io/skill-creation/optimizing-descriptions | Best practices for skill descriptions |
| **Evaluating Skills** | https://agentskills.io/skill-creation/evaluating-skills | Testing and quality metrics for skills |
| **Using Scripts** | https://agentskills.io/skill-creation/using-scripts | Bundling executable code in skills |

## Harness Platform APIs

### Official OpenAPI Specification
| Resource | URL | Details |
|----------|-----|---------|
| **OpenAPI Bundle (JSON)** | https://apidocs.harness.io/_bundle/index.json?download | 14MB, 1685 endpoints, OpenAPI 3.0.3 |
| **OpenAPI Bundle (YAML)** | https://apidocs.harness.io/_bundle/index.yaml?download | 10MB, alternative format |
| **OpenAPI Browser UI** | https://apidocs.harness.io | Interactive API explorer (read-only, no auth) |

### Harness API Modules (in official spec)
Documented in: `/home/unop/shalomb/agent-skills/skills/harness-idp/OPENAPI-XREF.md`

| Module | Endpoints | Key APIs |
|--------|-----------|----------|
| `v1` | 693 | IDP catalog, scorecards, plugins, layouts, templates |
| `ng` | 343 | Organizations, projects, connectors, RBAC |
| `ccm` | 207 | Cloud Cost Management |
| `iacm` | 168 | IaC Management |
| `gitops` | 145 | GitOps applications, clusters, agents |
| `code` | 138 | Code repositories, PRs, webhooks |
| `pipeline` | 85 | **Pipeline execution, triggers, input sets** |
| `gateway` | 90 | Autostopping, load balancing |
| `har` | 86 | Artifact Registry |
| `sto` | 78 | Security Testing Orchestration |
| `cv` | 77 | Continuous Verification |
| `cf` | 45 | Feature Flags |
| `authz` | 28 | ACL, permissions |
| `template` | 18 | Pipeline/stage templates |
| `dashboard` | 18 | Custom dashboards |
| `pm` | 24 | Policy Management |
| `audit` | 8 | Audit trail |

## GitHub Repositories

| Repository | URL | Purpose |
|------------|-----|---------|
| **agent-skills** | https://github.com/shalomb/agent-skills | Main agent skills framework repository |
| **Agent Skills (Official)** | https://github.com/agentskills/agentskills | Official Agent Skills specification repo |

## Frameworks and Standards Referenced

| Framework | URL | Purpose | Used In |
|-----------|-----|---------|---------|
| **Diataxis Framework** | https://diataxis.fr | Documentation framework (How-To, Reference, Explanation, Troubleshooting) | All docs/ structure |
| **OpenAPI 3.0.3 Spec** | https://spec.openapis.org/oas/v3.0.3 | API specification standard | Harness API discovery |
| **XDG Base Directory** | https://specifications.freedesktop.org/basedir-spec/latest/ | Linux config directory standard | Skill discovery paths |

## Related Tools and Implementations

### LLM/AI Platforms
| Tool | URL | Integration |
|------|-----|-------------|
| **Claude** | https://claude.ai | Primary AI model for skills |
| **Claude Code** | https://claude.ai/code | Claude in IDE integration |
| **Claude API** | https://api.anthropic.com | Programmatic API access |

### Development Tools Mentioned
| Tool | URL | Context |
|------|-----|---------|
| **GitHub CLI** | https://cli.github.com | Repository management (skills skill can use) |
| **Cursor IDE** | https://cursor.com | IDE that could integrate skills |
| **VSCode** | https://code.visualstudio.com | IDE for extensions |

### Build & Configuration Tools
| Tool | URL | Context |
|------|-----|---------|
| **Terraform** | https://www.terraform.io | IaC tool (integration context) |
| **Terraform Cloud** | https://app.terraform.io | TFC workspaces (skills can manage) |
| **AWS CloudFormation** | https://aws.amazon.com/cloudformation/ | IaC source format (reverse engineering) |

## Project-Specific Locations

### Local Filesystem
| Path | Purpose | Details |
|------|---------|---------|
| `~/shalomb/agent-skills/` | Main skills repository | All documentation and skills |
| `~/shalomb/agent-skills/docs/` | Documentation system | Diataxis-organized guides |
| `~/shalomb/agent-skills/skills/harness-idp/` | Harness IDP skill | Production-ready skill with OpenAPI discovery |
| `~/.agents/skills/` | User-level skills (convention) | Cross-client interoperability |
| `<project>/.agents/skills/` | Project-level skills (convention) | Repository-specific skills |

### Downloaded Resources
| File | Location | Size | Purpose |
|------|----------|------|---------|
| **PDF: The Complete Guide to Building Skills for Claude** | ~/Downloads/The-Complete-Guide-to-Building-Skill-for-Claude.pdf | 549KB | Source for docs conversion |
| **Extracted text** | ~/tmp-skills-guide.txt | 36KB | Plain text extraction |
| **agentskills.io page (text)** | /tmp/adding-skills-support.txt | ~20KB | Client implementation guide |

## Configuration Files Referenced

| Config | Location | Purpose |
|--------|----------|---------|
| **.agents/skills/** | `<project>/.agents/skills/` | Skill discovery path (convention) |
| **.env** | `~/.env` | Environment credentials (Harness account) |
| **justfile** | Project root | Build/test automation (GMSGQ project) |
| **.gitignore** | Skill directories | Exclude generated cache files |

## Documentation Cross-References

### Within This Project

#### How-To Guides
- [Create Your First Skill](../how-to/create-first-skill.md)
- [Implement Skills Support](../how-to/implement-skills-support.md) ← *NEW*
- [Structure a Skill](../how-to/structure-skill.md) (scaffolded)
- [Write Effective Instructions](../how-to/write-instructions.md) (scaffolded)
- [Test and Iterate](../how-to/test-and-iterate.md) (scaffolded)
- [Distribute Your Skill](../how-to/distribute-skill.md) (scaffolded)

#### Reference Documentation
- [YAML Frontmatter Specification](../reference/yaml-frontmatter.md)
- [URLs and Resources](../reference/urls-and-resources.md) ← *This file*
- [Skill Anatomy](../reference/skill-anatomy.md) (scaffolded)
- [Directory Structure](../reference/directory-structure.md) (scaffolded)
- [Success Criteria](../reference/success-criteria.md) (scaffolded)
- [Checklist](../reference/checklist.md) (scaffolded)

#### Explanations
- [Core Design Principles](../explanation/core-principles.md)
- [Architecture Patterns](../explanation/architecture-patterns.md)
- [Use Case Design](../explanation/use-case-design.md) (scaffolded)
- [MCP + Skills](../explanation/mcp-plus-skills.md) (scaffolded)
- [Quality Fundamentals](../explanation/quality-fundamentals.md) (scaffolded)

#### Troubleshooting
- [Common Issues](../troubleshooting/common-issues.md) (scaffolded)
- [Antipatterns](../troubleshooting/antipatterns.md) (scaffolded)
- [Debug Guide](../troubleshooting/debug-guide.md) (scaffolded)
- [Error Reference](../troubleshooting/error-reference.md) (scaffolded)

### Skill Documentation

#### Harness IDP Skill
- Location: `skills/harness-idp/`
- Main: `skills/harness-idp/README.md`
- Docs:
  - `SKILL.md` - Skill instructions
  - `OPENAPI-FALLBACK.md` - Discovery system guide
  - `OPENAPI-XREF.md` - Endpoint cross-reference (15 matched + 5 unmatched)
  - `EXAMPLES.md` - Real-world use cases
  - `TESTING.md` - Test structure and quality metrics
  - `QUICKSTART.md` - Quick start guide

### Project Documentation

#### Root Project
- `README.md` - Main project entry point
- `DOCUMENTATION-SUMMARY.md` - Project overview
- `DISCOVERY-SYSTEM.md` - OpenAPI discovery system overview

#### GMSGQ IaC Reverse Engineering Solution
- Location: `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/`
- AGENTS.md - Agent operations guide
- docs/README.md - Documentation index
- docs/explanation/architecture.md - Architecture decisions

## API Endpoints Documented

### Harness APIs (Cross-Referenced with Official Spec)

**Service Catalog APIs**:
- `GET /v1/entities` - List entities
- `GET /v1/entities/kinds` - List entity kinds

**Organization & Governance**:
- `GET /ng/api/organizations/{identifier}` - Get organization
- `GET /ng/api/connectors` - List connectors
- `GET /ng/api/apikey/aggregate` - Aggregate API keys

**User Settings**:
- `GET /ng/api/user-settings/get-user-preferences` - Get user preferences
- `PUT /ng/api/user-settings` - Update user settings

**Pipeline Discovery**:
- `GET /pipeline/api/pipelines/summary/{id}` - Get pipeline summary
- `GET /pipeline/api/pipelines/{id}` - Get pipeline details

**Pipeline Execution**:
- `POST /pipeline/api/pipelines/execution/summary` - List executions (body: YAML)
- `GET /pipeline/api/pipelines/execution/v2/{planExecutionId}` - Get execution

**Input Sets**:
- `POST /pipeline/api/inputSets/template` - Get input set template
- `POST /pipeline/api/inputSets/merge` - Merge input sets
- `POST /pipeline/api/pipeline/execute/{identifier}` - Execute pipeline

See: `skills/harness-idp/OPENAPI-XREF.md` for complete reference with parameters and schemas.

## Development Tools & CLI Commands

### Project-Level Tools
| Command | Purpose | Location |
|---------|---------|----------|
| `just preflight <apms-id>` | Validate prerequisites | GMSGQ project |
| `just generate <apms-id> <env>` | Generate Terraform | GMSGQ project |
| `just test` | Full test pipeline | GMSGQ project |
| `pi @adzic-index <file>` | BDD quality check | Pi skills |
| `pi @farley-index <file>` | Unit test quality check | Pi skills |

### Agent Skills Discovery
| Command | Purpose | Location |
|---------|---------|----------|
| `python3 openapi-discovery.py --search "keyword"` | Search APIs | `skills/harness-idp/` |
| `python3 openapi-discovery.py --endpoint PATH --method POST` | Get endpoint docs | `skills/harness-idp/` |
| `python3 openapi-discovery.py --list-modules` | List all modules | `skills/harness-idp/` |
| `python3 openapi-discovery.py --find-related TERM` | Find related endpoints | `skills/harness-idp/` |

## Testing & Quality Tools

| Tool | URL | Purpose |
|------|-----|---------|
| **pytest** | https://pytest.org | Python testing framework (units) |
| **behave** | https://behave.readthedocs.io | BDD feature testing |
| **pylint** | https://pylint.org | Code quality analysis |
| **black** | https://github.com/psf/black | Code formatting |

## Standards and Specifications

| Standard | URL | Application |
|----------|-----|-------------|
| **YAML 1.2** | https://yaml.org/spec/1.2 | Skill frontmatter |
| **Markdown** | https://commonmark.org | Skill body content |
| **JSON** | https://www.json.org | Configuration and API responses |
| **REST API Best Practices** | https://restfulapi.net | API design patterns |
| **Semantic Versioning** | https://semver.org | Skill versioning (e.g., 1.0.0) |

## Session Commits Reference

All work from this session is tracked in git commits:

| Commit | Message | Files | Scope |
|--------|---------|-------|-------|
| `aa8da93` | Add Diataxis-framework documentation structure | docs/ | Foundation |
| `fb851d7` | Add complete reference and explanation sections | docs/ | Content |
| `e2d5c42` | Add comprehensive documentation summary | DOCUMENTATION-SUMMARY.md | Meta |
| `df8daa1` | Add comprehensive project README | README.md | Project |
| `a031105` | Add comprehensive guide for implementing skills support | docs/how-to/ | *NEW* |

## How to Use This Reference

### Finding Information
1. **External resource?** → Check "Official Agent Skills Documentation" or "Harness Platform APIs"
2. **Internal doc?** → Check "Documentation Cross-References"
3. **Specific API?** → Check "API Endpoints Documented"
4. **Local file?** → Check "Project-Specific Locations"

### Contributing to URLs
When adding new resources:
1. Verify the URL works
2. Add to appropriate section with purpose/details
3. Link from relevant docs where applicable
4. Update commit reference if creating new documentation

### Keeping URLs Updated
- Review quarterly for broken links
- Test all external URLs before major releases
- Update links when resources move or change
- Document deprecations and redirects

---

**Last Updated**: 2026-03-09  
**Scope**: Complete session with 5+ documents created  
**Total URLs**: 50+ resources across multiple categories  
**Status**: Active and maintained

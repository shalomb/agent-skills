## 🔍 Terraform Import Validation Assessment ({DATE})

{CONTEXT}

### Repositories
- [{REPO_NAME}]({REPO_URL})

### TFC Plan Status

| Env | Workspace | Branch | PR | Run Status | Import | Add | Change | Destroy | Assessment |
|-----|-----------|--------|-----|------------|--------|-----|--------|---------|------------|
|{ENV}|`{WORKSPACE}`|[`{BRANCH}`]({REPO_URL}/tree/{BRANCH})|[#{PR}]({REPO_URL}/pull/{PR})|[{STATUS}](https://app.terraform.io/app/{TFC_ORG}/{WORKSPACE}/runs/{RUN_ID})|{IMPORT}|{ADD}|{CHANGE}|{DESTROY}|{ASSESSMENT}|

<!-- Repeat rows per environment -->

### Summary

- **Total resources to import**: {TOTAL_IMPORTS}
- **Additions**: {TOTAL_ADDS} ({ADD_EXPLANATION})
- **Changes**: {TOTAL_CHANGES} — {CHANGE_EXPLANATION}
- **Destroys**: {TOTAL_DESTROYS}
- **Real infrastructure changes**: **{REAL_CHANGES}** {EMOJI}

### Change Classification

<!-- Classify each resource change using terraform-plan-parser mutation filter.
     Categories:
     - Tag normalization
     - Import state population (null→value, no prior state)
     - Provider default (null→false for boolean attrs)
     - Internal resource (terraform_data creates)
     - Real mutation (actual attribute change — requires justification)
-->

| # | Resource | Change | Category | Action |
|---|----------|--------|----------|--------|
| {N} | {RESOURCE} | {CHANGE_DESC} | {CATEGORY} | ✅ Accept / ⚠️ Investigate / 🔴 Block |

### 🔧 Fixes Applied

1. [`{SHA}`]({REPO_URL}/commit/{SHA}) — {COMMIT_SUBJECT}

### ⚠️ Action Required

- {ACTION_ITEM}

---
*Plans verified via `terraform plan` CLI + `TerraformPlainTextPlanParser`*

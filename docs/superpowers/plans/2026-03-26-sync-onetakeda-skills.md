# Sync oneTakeda Skills to agent-skills Repo

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sync skills from `~/oneTakeda/**/.github/skills/` into `~/shalomb/agent-skills/skills/`, applying sanitization for public use and organizing into logical atomic commits.

**Architecture:** Each commit is self-contained and semantically meaningful — either updating an existing skill or adding a new one. Sensitive content (org-specific names, hardcoded IDs, internal URLs) is replaced with generic placeholders per AGENTS.md policy before commit.

**Tech Stack:** bash, git, diff, sed, grep

---

## Summary of Findings

### Skills to UPDATE (exist in both places, canonical is behind or has diverged)

| Skill | Status | Action |
|-------|--------|--------|
| `github-cli` | Canonical has **more** content than oneTakeda versions (937 vs 742 lines in reference). BUT the uncommitted working-tree change adds Projects V2 content to the reference. The `cloud-engineering` version has a Projects V2 section in SKILL.md itself that should be merged/reviewed. | Commit the staged Projects V2 reference additions; evaluate SKILL.md improvements |
| `tfc-api` | The oneTakeda versions (`clouddevsecops`, `cloud-engineering`, `bb-template`) are **older/stripped** versions; canonical is authoritative. No action needed from oneTakeda → canonical direction. | No sync needed (canonical is newer) |
| `terraform-dev` | Canonical (`Terraform module`) is the generalized version; oneTakeda versions are either BB-specific (`Building Block`) or use a different `tf-watcher` paradigm (file-watching vs Makefile). Canonical is the authoritative generalized form. | No sync needed |
| `adzic-index`, `farley-index`, `harness-idp`, `humanizer`, `web-to-markdown` | **Identical** — no changes needed | Skip |

### NEW Skills to ADD from oneTakeda (needs sanitization)

#### Group A: Clean / No Sensitive Content
- `apms-orchestration-debugger` — single source, no sensitive refs
- `aws-import-planner` — single source, no sensitive refs
- `diataxis-doc-validator` — single source, no sensitive refs
- `hcl-diff-validator` — single source, no sensitive refs
- `bb-upgrade-advisor` — single source, no sensitive refs
- `mode1` — single source, no sensitive refs (APMS-ID pattern, phase-driven workflow)
- `request-capture` — single source + references/, no sensitive refs

#### Group B: Needs Light Sanitization (example/placeholder refs to org)
- `review-inline-comments` — `oneTakeda/<repo>` and `oneTakeda/terraform-aws-RDS` used as examples; references/comment-templates.md mentions "Takeda naming conventions"
- `review-feedback-summary` — references/feedback-template.md mentions "Takeda pattern" once

#### Group C: Too Org-Specific — Skip for Now
(requires deep refactoring to generalize — separate effort)
- `takeda-building-blocks`, `takeda-enterprise-cloud`, `terraform-enterprise-cloud`
- `bb-patch`, `bb-quality`, `bb-breaking-changes`, `bb-ci-checks`, `bb-develop`, `bb-document`, `bb-validate`, `bb-workflow`, `bb-discovery`
- `cfn-analyzer`, `compliance`, `devops-repo-automation`, `kedb`, `mode1-cloud-request`, `tf-workspace-sync`
- `adr-creator`, `review-inline-comments` (deep Takeda patterns in references)

---

## Commit Plan

### Commit 1: Commit the staged github-cli Projects V2 reference additions

**Files:**
- Modify: `skills/github-cli/references/github-cli-reference.md` (already staged/modified)

- [ ] **Step 1: Review the working-tree change**
  ```bash
  cd ~/shalomb/agent-skills
  git diff skills/github-cli/references/github-cli-reference.md
  ```
  Verify it sanitizes the org-specific examples (the diff shows `oneTakeda/gmsgq-dad-...` → `YOUR_ORG/YOUR_REPO`) and adds the Projects V2 section.

- [ ] **Step 2: Stage and commit**
  ```bash
  git add skills/github-cli/references/github-cli-reference.md
  git commit -m "docs(github-cli): Add Projects V2 reference and sanitize org-specific examples"
  ```

---

### Commit 2: Add `apms-orchestration-debugger` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/apms-orchestration-debugger/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/apms-orchestration-debugger \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/apms-orchestration-debugger/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/apms-orchestration-debugger/
  git commit -m "feat(skills): Add apms-orchestration-debugger skill"
  ```

---

### Commit 3: Add `aws-import-planner` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/aws-import-planner/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/aws-import-planner \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/aws-import-planner/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/aws-import-planner/
  git commit -m "feat(skills): Add aws-import-planner skill"
  ```

---

### Commit 4: Add `diataxis-doc-validator` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/diataxis-doc-validator/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/diataxis-doc-validator \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/diataxis-doc-validator/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/diataxis-doc-validator/
  git commit -m "feat(skills): Add diataxis-doc-validator skill"
  ```

---

### Commit 5: Add `hcl-diff-validator` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/hcl-diff-validator/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/hcl-diff-validator \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/hcl-diff-validator/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/hcl-diff-validator/
  git commit -m "feat(skills): Add hcl-diff-validator skill"
  ```

---

### Commit 6: Add `bb-upgrade-advisor` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/bb-upgrade-advisor/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-clouddevsecops-iac-reveng-solution/.github/skills/bb-upgrade-advisor \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/bb-upgrade-advisor/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/bb-upgrade-advisor/
  git commit -m "feat(skills): Add bb-upgrade-advisor skill"
  ```

---

### Commit 7: Add `mode1` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower/.github/skills/mode1/`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower/.github/skills/mode1 \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/mode1/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/mode1/
  git commit -m "feat(skills): Add mode1 infrastructure request orchestration skill"
  ```

---

### Commit 8: Add `request-capture` skill

**Source:** `/home/unop/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/request-capture/`
(includes `references/output-schema.md`)

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/request-capture \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Verify no sensitive content**
  ```bash
  grep -rn "takeda\|Takeda\|oneTakeda\|glpat\|secret\|password" \
    ~/shalomb/agent-skills/skills/request-capture/
  ```
  Expected: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/request-capture/
  git commit -m "feat(skills): Add request-capture skill with output schema reference"
  ```

---

### Commit 9: Add `review-feedback-summary` skill (with sanitization)

**Source:** `/home/unop/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/review-feedback-summary/`
**Sensitive items to fix:**
- `references/feedback-template.md` line ~104: `"Takeda pattern"` → `"org pattern"`

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/review-feedback-summary \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Sanitize — replace org-specific references**
  ```bash
  # Find and fix sensitive refs
  grep -rn "Takeda\|takeda\|oneTakeda" ~/shalomb/agent-skills/skills/review-feedback-summary/
  # Fix any found with sed:
  sed -i 's/Takeda pattern/org pattern/g' \
    ~/shalomb/agent-skills/skills/review-feedback-summary/references/feedback-template.md
  # Verify clean
  grep -rn "Takeda\|takeda\|oneTakeda" ~/shalomb/agent-skills/skills/review-feedback-summary/
  ```
  Expected after fix: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/review-feedback-summary/
  git commit -m "feat(skills): Add review-feedback-summary skill with feedback template reference"
  ```

---

### Commit 10: Add `review-inline-comments` skill (with sanitization)

**Source:** `/home/unop/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/review-inline-comments/`
**Sensitive items to fix:**
- `SKILL.md` line 12: `REPO=oneTakeda/<repo>` → `REPO=ORG/<repo>`
- `SKILL.md` line 82: `oneTakeda/terraform-aws-RDS` → `ORG/terraform-aws-RDS`
- `references/comment-templates.md`: `oneTakeda/terraform-BuildingBlock-Template` → `ORG/terraform-BuildingBlock-Template`
- `references/comment-templates.md`: "Takeda naming conventions" → "org naming conventions"
- `references/comment-templates.md`: "Takeda accounts" → "org accounts"

- [ ] **Step 1: Copy skill**
  ```bash
  cp -r ~/oneTakeda/gmsgq-dad-cloud-engineering-context/.github/skills/review-inline-comments \
       ~/shalomb/agent-skills/skills/
  ```

- [ ] **Step 2: Sanitize**
  ```bash
  # SKILL.md fixes
  sed -i 's|REPO=oneTakeda/<repo>|REPO=ORG/<repo>|g' \
    ~/shalomb/agent-skills/skills/review-inline-comments/SKILL.md
  sed -i 's|oneTakeda/terraform-aws-RDS|ORG/terraform-aws-RDS|g' \
    ~/shalomb/agent-skills/skills/review-inline-comments/SKILL.md

  # references/comment-templates.md fixes
  sed -i 's|oneTakeda/terraform-BuildingBlock-Template|ORG/terraform-BuildingBlock-Template|g' \
    ~/shalomb/agent-skills/skills/review-inline-comments/references/comment-templates.md
  sed -i 's/Takeda naming conventions/org naming conventions/g' \
    ~/shalomb/agent-skills/skills/review-inline-comments/references/comment-templates.md
  sed -i 's/Takeda accounts/org accounts/g' \
    ~/shalomb/agent-skills/skills/review-inline-comments/references/comment-templates.md

  # Verify clean
  grep -rn "Takeda\|takeda\|oneTakeda" ~/shalomb/agent-skills/skills/review-inline-comments/
  ```
  Expected after fix: no output

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/review-inline-comments/
  git commit -m "feat(skills): Add review-inline-comments skill with comment templates reference"
  ```

---

### Commit 11: Update skills/README.md

Add all new skills to the README listing.

- [ ] **Step 1: View current README**
  ```bash
  cat ~/shalomb/agent-skills/skills/README.md | head -50
  ```

- [ ] **Step 2: Add new skills to the listing** (alphabetically in appropriate section)
  New skills to add:
  - `apms-orchestration-debugger`
  - `aws-import-planner`
  - `bb-upgrade-advisor`
  - `diataxis-doc-validator`
  - `hcl-diff-validator`
  - `mode1`
  - `request-capture`
  - `review-feedback-summary`
  - `review-inline-comments`

- [ ] **Step 3: Commit**
  ```bash
  cd ~/shalomb/agent-skills
  git add skills/README.md
  git commit -m "docs(skills): Update README with 9 new skills"
  ```

---

## Skills NOT Synced (and why)

These remain in oneTakeda repos only. They need a dedicated generalization effort:

| Skill | Reason |
|-------|--------|
| `takeda-building-blocks` | Core concept is Takeda-specific (BB registry, org naming, TFC org) |
| `takeda-enterprise-cloud` | AWS topology is 100% org-specific |
| `terraform-enterprise-cloud` | References Takeda TFC org throughout |
| `bb-patch`, `bb-quality`, `bb-breaking-changes`, `bb-ci-checks`, `bb-develop`, `bb-document`, `bb-validate`, `bb-workflow`, `bb-discovery` | Deeply tied to Takeda BB ecosystem |
| `cfn-analyzer` | References Takeda BB registry for mapping |
| `compliance` | SOPs and regulatory framework are Takeda-specific |
| `devops-repo-automation` | Hardcoded to `oneTakeda/devops-repo-automation` repo |
| `kedb` | Tied to `oneTakeda/terraform-Takeda-KEDB` repo |
| `mode1-cloud-request` | ServiceNow RITM patterns and Takeda SLAs |
| `adr-creator` | References `@oneTakeda/platform-architecture` team |
| `tf-workspace-sync` | References Takeda TFC org |
| `review-inline-comments/references` | Deep Takeda BB naming in templates |

---

## Notes

- The `github-cli` cloud-engineering version has a sophisticated Projects V2 section in SKILL.md that references a `project-config.sh` file (org-specific). The Projects V2 **patterns** are generic and have been added to the canonical reference file (Commit 1). The repo-specific IDs in `project-config.sh` are not suitable for the public repo.
- `terraform-dev` in oneTakeda uses two paradigms: `tf-watcher` (file-watching daemon) and Makefile. The canonical uses Makefile. These diverged intentionally and the canonical is the generalized version.
- `tfc-api` in oneTakeda lacks the team/project access management content — the canonical is more complete.

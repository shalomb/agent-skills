# TargetProcess Team Scenarios

Advanced workflows for Lead/Principal Engineers and Agile teams to manage Program Increments (PIs), Program/Team Objectives, and overall health.

## 1. ART Dashboarding (The Program Pulse)

High-level view of current and upcoming program increments for an entire Agile Release Train (ART).

### Use When
- Starting PI planning
- Reviewing ART-wide objectives and commitments
- Identifying participation levels across 20+ teams

### PI Planning Workflow (DAD/GMSGQ)
```bash
# 1. Create Feature linked to an objective atomically (Python client)
python -c "
from tpcli_pi.core.api_client import TPAPIClient
c = TPAPIClient()
f = c.create_feature('IaCRE', parent_epic_id=0,
    team_id=2022903, release_id=2033368, objective_id=2284608)
print(f'Created Feature Id: {f.id}')
"

# 2. Or via tpcli CLI (two-step)
tpcli plan create Feature --data '{"Name":"IaCRE","Team":{"Id":2022903},"Release":{"Id":2033368}}'
tpcli plan link Feature <feature_id> TeamPIObjective 2284608

# 3. Verify
tpcli get TeamPIObjective 2284608
# Check Features sub-collection in response
```

### Command Pattern
```bash
# View full dashboard for an ART
tpcli ext art-dashboard --art "Data, Analytics and Digital"

# Filter to current or upcoming PI
tpcli ext art-dashboard --art "Data, Analytics and Digital" --pi current
tpcli ext art-dashboard --art "Data, Analytics and Digital" --pi upcoming
```

### Key Metrics
- **Current vs. Next Release**: Status, dates, and timeline.
- **Team Participation**: List of all teams with their objective counts and status.
- **Program Objectives**: Summary of high-level objectives grouped by release.
- **Health Indicators**: Total teams, total objectives, and at-risk items.

---

## 2. Team Deep Dive (Capacity & Commitment)

Drill down into a specific team to understand their PI commitments, capacity, and potential blockers.

### Use When
- Conducting team-level planning sessions
- Reviewing team health and overcommitment risks
- Investigating historical performance

### Command Pattern
```bash
# Summary view of team status — use FULL team name
tpcli ext team-dashboard --team "DAD - Fusion - Cloud Enablement & Delivery"

# Deep dive into team capacity and risks
tpcli ext team-deep-dive --team "DAD - Fusion - Cloud Enablement & Delivery" --pi current

# Show specific aspects
tpcli ext team-deep-dive --team "DAD - Fusion - Cloud Enablement & Delivery" --show capacity
tpcli ext team-deep-dive --team "DAD - Fusion - Cloud Enablement & Delivery" --show risks
tpcli ext team-deep-dive --team "DAD - Fusion - Cloud Enablement & Delivery" --show features

# PI-to-PI objective comparison
tpcli ext compare --release "DAD: PI-1/26" --previous "DAD: PI-4/25" \
  --team "DAD - Fusion - Cloud Enablement & Delivery"
tpcli ext compare --release "DAD: PI-1/26" --format markdown

# If previous-release is set in context config, --previous is optional:
tpcli ext compare --release "DAD: PI-1/26"
```

### Finding teams by partial name (API workaround)
```bash
# TP API rejects --where "Name like '%x%'" for Teams; use find instead:
tpcli find team "Cloud Enablement"
tpcli find team --exact "Cloud Enablement & Delivery"
```

### Key Metrics
- **Workload**: Effort per person (points).
- **Risk Assessment**: Skills gaps (e.g., "Need K8s expertise"), resource risks, and description quality.
- **Historical Context**: Completion rates and average effort/objective from previous PIs.

---

## 3. Objective Deep Dive (Dependency & Risk Mapping)

In-depth analysis of individual PI objectives, including linked features, Jira correlation, and risks.

### Use When
- Troubleshooting a specific blocked objective
- Mapping technical or schedule risks
- Verifying Jira sync status for an objective

### Command Pattern
```bash
# Full objective report
tpcli ext objective-deep-dive --objective 2029314

# Drill into specific categories
tpcli ext objective-deep-dive --objective 2029314 --show dependencies
tpcli ext objective-deep-dive --objective 2029314 --show risks
tpcli ext objective-deep-dive --objective 2029314 --show jira
```

### Key Insights
- **Cross-Objective Dependencies**: Blocks/Blocked-by relationships across teams.
- **Risk Analysis**: Technical, Schedule, Resource, and Capacity risks with mitigations.
- **Jira Correlation**: Matching Jira Epics (e.g., "EX-100") and their status.
- **Decision History**: Status changes and key stakeholder comments.

---

## 4. Release/PI Status Report (The Executive Summary)

Tracking the status of a program increment across all participating teams.

### Use When
- Reporting PI progress to stakeholders
- Identifying cross-team blockers midway through a PI
- Comparing current PI performance against historical baselines

### Command Pattern
```bash
# Comprehensive PI status summary
tpcli ext release-status --release "PI-4/25"

# Executive summary format
tpcli ext release-status --release "PI-4/25" --format summary

# View inter-team blockers
tpcli ext release-status --release "PI-4/25" --show dependencies
```

### Key Metrics
- **PI Progress**: % objectives completed vs. pending.
- **Effort Tracking**: Total estimated points and velocity trends.
- **Blocker Graph**: Visualization of inter-team dependencies ("Team A waiting on Team B").

---

## Output Formats & Integration

All scenario commands support standard formats for reporting:

| Format | Command Flag | Use Case |
|--------|--------------|----------|
| **Markdown** | `--format markdown` | Sharing via Slack/Teams or including in docs |
| **JSON** | `--format json` | Programmatic processing or custom dashboards |
| **Summary** | `--format summary` | Executive/Management reporting |
| **CSV** | `--format csv` | Data analysis in Excel/Google Sheets |

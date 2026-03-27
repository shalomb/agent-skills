---
name: meeting-notes
description: Process meeting transcripts (VTT format) to extract meeting minutes, action items, and decisions. Use when given transcript files or asked to create meeting documentation, extract action items, or record decisions.
---

# Meeting Notes Skill

Process Microsoft Teams meeting transcripts (VTT format) to extract meeting minutes, action items, and decisions. Optionally update GitHub issues, Jira tickets, and other systems with findings.

## Purpose

Convert raw Teams meeting transcripts into structured, actionable meeting documentation:
- **Meeting Minutes**: Summary of discussion, decisions, context
- **Action Items**: Who-what-when tasks with owners
- **Follow-ups**: Questions, blockers, escalations
- **Decisions**: Documented decisions with rationale
- **Attendees & Time**: Metadata extraction

## Capabilities

1. **Transcript Parsing**: Read VTT (WebVTT) format files, extract speakers and content
2. **Content Analysis**: Identify decisions, actions, and key discussions using NLP
3. **Meeting Minutes Generation**: Structured markdown with sections
4. **Action Extraction**: Owner + Description + Due Date pattern recognition
5. **Decision Documentation**: Track decisions with context and implications
6. **Follow-up Integration**: Optional updates to GitHub issues, Jira tickets, Slack messages
7. **Interactive Prompts**: Ask user which systems to update and how

## Input

**Required**:
- VTT (WebVTT) transcript file path
- Meeting context (title, date, participants)

**Optional**:
- GitHub issue number (to update)
- Jira ticket key (to update)
- Slack channel (to post summary)
- Custom output format preferences

## Output

**Primary**: Structured markdown meeting minutes with sections:
- Meeting Header (title, date, attendees, duration)
- Executive Summary (1-2 sentence overview)
- Decisions (bulleted list with owners)
- Action Items (table format with owner/description/due date)
- Key Discussion Points (by topic)
- Follow-ups (open questions, blockers, escalations)
- Attendees List (with speaker counts)

**Secondary** (optional):
- GitHub issue comment (if issue specified)
- Jira ticket update (if ticket specified)
- Slack message (if channel specified)

## Usage

### Basic: Parse and Generate Minutes

```bash
# Agent command:
# "Process the Teams transcript from my ChemDraw architecture meeting"
# or
# "Extract action items from weekly sync meeting (meeting.vtt)"

Agent steps:
1. User provides VTT file path (or pasts content)
2. Agent parses transcript
3. Agent extracts: speakers, timestamps, content
4. Agent analyzes content for decisions/actions
5. Agent generates structured minutes in markdown
6. Agent asks: "Would you like to update GitHub/Jira with these findings?"
```

### Advanced: Update Multiple Systems

```bash
Agent workflow:
1. Parse transcript
2. Generate minutes
3. Ask user:
   ✓ "I found 5 action items. Update GitHub issue #123?"
   ✓ "I found 3 decisions. Create Jira ticket?"
   ✓ "I found 2 blockers. Post to #architecture Slack channel?"
4. Execute user's selections
5. Post results with links
```

## Features

### Automatic Detection

- **Speakers**: Identify unique participants by name
- **Decisions**: Pattern matching: "we decided", "we will", "agreed", "committed to"
- **Actions**: Pattern matching: "need to", "follow up", "action item", "@mention will"
- **Blockers**: Pattern matching: "blocked", "waiting for", "dependency on", "need X before"
- **Questions**: Pattern matching: "?", "anyone know", "does anyone", "how do we"

### Smart Grouping

- Group decisions by topic
- Group actions by owner
- Group discussions by theme
- Calculate speaker participation (who spoke most)
- Identify key participants (people mentioned frequently)

### Confidence Scoring

- Decision confidence: HIGH/MEDIUM/LOW based on language certainty
- Action clarity: HIGH/MEDIUM/LOW based on specificity (owner + deadline present)
- Discussion relevance: Score discussion sections by importance

## VTT File Format

```vtt
WEBVTT

00:00:01.000 --> 00:00:05.000
Speaker: Hello, this is the architecture review meeting

00:00:05.100 --> 00:00:10.500
Speaker: We need to decide on the database design

00:00:10.600 --> 00:00:15.200
Other Speaker: I think PostgreSQL is the right choice

...
```

Agent parses:
- Timestamps: 00:00:01.000 format
- Speaker name: Before colon
- Content: After speaker name

## Interactive Prompts

After generating minutes, agent asks user:

```
I've processed the transcript and extracted:
- 3 decisions (PostgreSQL selected, 2 others)
- 5 action items (owners: @alice, @bob, @charlie)
- 2 blockers (need X approval, waiting for Y data)

What would you like to do?

1. [ ] Post as GitHub comment on issue #123
2. [ ] Create Jira ticket for tracking
3. [ ] Update Slack thread
4. [ ] Save minutes to file (minutes-2025-03-11.md)
5. [ ] All of the above
6. [ ] Nothing (just show me the output)

Enter your selections (comma-separated, e.g., 1,3,4):
```

## System Integration

### GitHub Integration

If issue number provided:
```bash
# Generate comment with:
- Meeting link/summary
- Action items table
- Decisions list
- @mention owners for actions

gh issue comment {issue_number} --body "{formatted_minutes}"
```

### Jira Integration

If Jira key provided:
```bash
# Create subtasks for each action item:
- Parent: {jira_key}
- Subtasks: One per action item
- Fields: Assignee, Due Date, Description

jira issue create --parent {key} --type Subtask ...
```

### Slack Integration

If Slack channel provided:
```bash
# Post thread with:
- Summary as main message
- Action items in thread reply
- Decisions in thread reply
- Links to GitHub/Jira tickets

slack chat postMessage --channel {channel} ...
```

## Example: Architecture Review Meeting

### Input VTT (partial)
```vtt
WEBVTT

00:00:15.200 --> 00:00:20.100
Sarah: Welcome to the ChemDraw architecture review. Today we're deciding on the database design.

00:00:20.200 --> 00:00:25.500
John: I think PostgreSQL is the best choice because of JSON support and GxP compliance.

00:00:25.600 --> 00:00:30.200
Sarah: We agreed on PostgreSQL. John, can you document the rationale by Friday?

00:00:30.300 --> 00:00:35.100
John: Yes, I'll have that ready.

00:00:35.200 --> 00:00:40.600
Alice: I have a blocker - we need security team approval for the encryption approach.

00:00:40.700 --> 00:00:45.300
Sarah: Alice, can you reach out to security? Let's follow up Monday.
```

### Agent Output

```markdown
# Meeting Minutes: ChemDraw Architecture Review

**Date**: 2025-03-11  
**Time**: 15:00 - 16:30 UTC  
**Duration**: 90 minutes  
**Attendees**: Sarah (host), John, Alice  

## Executive Summary
Team decided on PostgreSQL as database engine for ChemDraw GxP system, prioritizing JSON support and regulatory compliance. One blocker identified: security team approval needed for encryption approach.

## Decisions

1. **Database Engine: PostgreSQL** ✅
   - Rationale: JSON support, GxP compliance, mature ecosystem
   - Owner: John
   - Confidence: HIGH
   
2. **Encryption Approach: Pending Security Review** ⏳
   - Status: Blocked (awaiting security team input)
   - Owner: Alice
   - Follow-up: By Monday

## Action Items

| Owner | Action | Due Date | Status |
|-------|--------|----------|--------|
| John | Document PostgreSQL rationale & design | 2025-03-14 (Fri) | Not Started |
| Alice | Get security team approval for encryption | 2025-03-17 (Mon) | Blocked |
| Sarah | Coordinate architecture review with security | 2025-03-17 (Mon) | Not Started |

## Key Discussion Points

### Database Design Rationale
- PostgreSQL chosen over MySQL due to:
  - Native JSON/JSONB support
  - GxP compliance track record
  - Mature tooling ecosystem
  - Better performance for complex queries
  
### Security Concerns
- Encryption approach needs formal security review
- Will impact schema design
- Need to address before moving to implementation

## Blockers & Follow-ups

1. **Blocker**: Security team approval for encryption approach
   - Owner: Alice
   - Due: Monday 2025-03-17
   - Impact: Blocks implementation phase

2. **Follow-up**: Confirm PostgreSQL version support for GxP environments
   - Owner: John
   - Due: Friday 2025-03-14

## Participants

- **Sarah** (3 speaking turns) — Meeting facilitator
- **John** (2 speaking turns) — Database architect
- **Alice** (2 speaking turns) — Security owner
```

### Agent Prompt to User

```
I've extracted the following from your ChemDraw architecture meeting:

✅ 2 decisions (PostgreSQL, encryption approach TBD)
✅ 3 action items (John, Alice, Sarah)
✅ 1 blocker (security approval needed)
✅ 2 discussion topics (database design, security concerns)

What would you like to do?

1. [ ] Post minutes to GitHub issue #456 (ChemDraw Architecture)
2. [ ] Create Jira subtasks for action items
3. [ ] Update Slack #architecture channel
4. [ ] Save to file (minutes-2025-03-11-architecture-review.md)
5. [ ] Create new GitHub issue to track blocker

Enter selections (1,2,3,4,5) or press Enter to skip:
```

## Related Skills & Tools

- `github-cli` - For posting to GitHub issues
- `jira-api` - For creating Jira tickets
- `slack-api` - For posting to Slack channels
- `markdown` - For formatting output

## File Format Support

- **VTT (WebVTT)**: Primary format from Teams
- **SRT (SubRip)**: Alternative subtitle format
- **TXT (Plain text)**: Paste content directly
- **M4A/WAV**: Transcribe using cloud APIs (future)

## Limitations & Notes

- Accuracy depends on transcript quality (requires good speaker identification)
- Confidence scoring is heuristic-based (may miss context-dependent decisions)
- Custom integrations may require API keys (GitHub, Jira, Slack)
- Large meetings (30+ participants) may produce lengthy minutes
- Technical discussions may require domain knowledge to properly categorize

## Configuration

```yaml
# ~/.config/meeting-notes/config.yaml

# Default output format
output_format: markdown

# Auto-detect systems to update
auto_detect: false

# Confidence thresholds
decision_confidence_threshold: 0.6
action_clarity_threshold: 0.5

# Integrations (optional)
github:
  enabled: true
  org: {YOUR_GITHUB_ORG}
jira:
  enabled: true
  instance: {YOUR_ORG}.atlassian.net
slack:
  enabled: true
  workspace: {YOUR_SLACK_WORKSPACE}
```

## Troubleshooting

**Q: Transcript quality is poor (bad speaker identification)**
A: Manually provide speaker list in first line of VTT, agent will use it

**Q: Too many false-positive actions detected**
A: Increase `action_clarity_threshold` in config; agent will be stricter

**Q: Missing important decision/action**
A: Review transcript manually; agent may have low confidence. Ask user to add it

**Q: Want to update multiple GitHub issues with same minutes**
A: Agent will ask: "Post to issue #1, #2, and #3?"

---

**Maintained by**: contributors  
**Version**: 1.0  
**Last Updated**: 2025-03-11

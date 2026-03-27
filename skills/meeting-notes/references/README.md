# Meeting Notes Skill

Convert MS Teams meeting transcripts into actionable meeting minutes with decisions, actions, and follow-ups. Optionally integrate with GitHub, Jira, and Slack.

## Quick Start

### Install

```bash
# Already in ~/.config/meeting-notes/
# No installation needed — ready to use
```

### Basic Usage

```bash
# Process a Teams transcript
agent: "Process the Teams meeting transcript from my architecture review"

or

agent: "Extract action items from this meeting (transcript.vtt)"
```

Agent will:
1. Parse the VTT transcript
2. Extract decisions, actions, blockers
3. Generate markdown minutes
4. Ask what to do next (GitHub/Jira/Slack/file?)

### With GitHub Integration

```bash
agent: "Process ChemDraw architecture meeting and post minutes to GitHub issue #456"
```

Agent will:
1. Parse transcript
2. Extract findings
3. Post formatted comment to GitHub issue
4. Create action items as GitHub issue mentions (@owner)

### With Jira Integration

```bash
agent: "Process architecture meeting and create Jira subtasks for action items"
```

Agent will:
1. Parse transcript
2. Extract action items
3. Create subtask in Jira for each action
4. Assign to owners with due dates

### With Slack Integration

```bash
agent: "Process meeting and post summary to #architecture with action items"
```

Agent will:
1. Parse transcript
2. Extract findings
3. Post summary as main message
4. Reply in thread with action items, decisions, blockers

## Files in This Skill

- **SKILL.md** — Full skill documentation and capabilities
- **extract-minutes.prompt.md** — Detailed extraction prompt for Claude
- **config.yaml** — Configuration options
- **examples/** — Example transcripts and outputs (optional)

## Configuration

Edit `config.yaml` to customize:

```yaml
# Enable/disable GitHub, Jira, Slack integration
integrations:
  github:
    enabled: true
  jira:
    enabled: true
  slack:
    enabled: true

# Change output format
output_format: markdown  # or json, or both

# Adjust confidence thresholds
decision_confidence_threshold: 0.6
action_clarity_threshold: 0.5
```

## Supported Input Formats

- **VTT (WebVTT)**: Native Teams transcript format
- **SRT (SubRip)**: Subtitle format
- **TXT**: Plain text with timestamps
- **Paste directly**: Copy/paste transcript content

## Output Examples

### Meeting Minutes (Markdown)

```markdown
# Meeting Minutes: Architecture Review

**Date**: 2025-03-11
**Duration**: 90 minutes
**Attendees**: Sarah, John, Alice

## Executive Summary
Team decided on PostgreSQL for GxP database, with security approval as critical blocker.

## Decisions
1. PostgreSQL as primary database (Owner: John) — HIGH confidence
2. Encryption approach pending (Owner: Alice) — MEDIUM confidence

## Action Items
| Owner | Action | Due | Status |
|-------|--------|-----|--------|
| John | Document schema rationale | 2025-03-14 | Not Started |
| Alice | Security team approval | 2025-03-17 | Blocked |

## Blockers
- 🚫 Security approval needed for encryption approach
```

### GitHub Comment

Agent posts to GitHub issue:

```markdown
## 📋 Meeting Minutes: Architecture Review

**Date**: 2025-03-11 | **Duration**: 90 min | **Attendees**: Sarah, John, Alice

### Decisions
- ✅ PostgreSQL selected as primary database
- ⏳ Encryption approach pending security review

### Action Items
- @john — Document PostgreSQL schema rationale (by Friday)
- @alice — Get security team approval (by Monday) 🚫 **BLOCKED**

### Blockers
- Security team approval needed for encryption approach

### Key Points
- PostgreSQL chosen for JSON support and GxP compliance
- Need to address encryption before schema finalization
```

### Jira Subtasks

Agent creates subtasks under parent issue:

```
Parent: DAD-123 (ChemDraw Architecture)

Subtask 1:
- Title: Document PostgreSQL schema rationale
- Assignee: John
- Due Date: 2025-03-14
- Status: To Do

Subtask 2:
- Title: Get security team approval for encryption
- Assignee: Alice
- Due Date: 2025-03-17
- Status: Blocked
- Blocker: Awaiting security team
```

### Slack Thread

Agent posts summary, then replies in thread:

```
Main Message:
📋 Architecture Review Meeting Summary

✅ 2 Decisions | 📝 3 Actions | 🚫 1 Blocker | ⏱️ 90 minutes

---

Thread Reply 1:
**Action Items**
• @john — Document schema (Friday)
• @alice — Security approval (Monday) 🚫
• @sarah — Follow up coordination (Monday)

Thread Reply 2:
**Key Decisions**
• PostgreSQL selected for JSON + GxP support
• Encryption approach pending approval

Thread Reply 3:
**Blockers & Follow-ups**
• 🚫 Security team approval for encryption
• ❓ Confirm PostgreSQL version support
```

## Workflow: Interactive Prompts

After extracting meeting content, agent asks:

```
✅ Meeting Analysis Complete

Findings:
  - 2 decisions
  - 3 action items  
  - 1 blocker
  - 4 follow-ups
  - 60 min speaking time

What would you like to do?

1. [ ] Post to GitHub issue #456
2. [ ] Create Jira subtasks
3. [ ] Post to Slack #architecture
4. [ ] Save to file
5. [ ] All of the above
6. [ ] Show me the markdown first

Enter selections (comma-separated) or press Enter to skip:
```

User selects options, agent executes and reports:

```
✅ Updated GitHub issue #456 with minutes comment
✅ Created 3 Jira subtasks assigned to owners
✅ Posted to Slack #architecture (3 messages in thread)
✅ Saved minutes to ~/meeting-minutes/minutes-2025-03-11-architecture-review.md

Links:
- GitHub: https://github.com/ORG/.../issues/456#comment-12345
- Jira: https://{YOUR_ORG}.atlassian.net/browse/DAD-123
- Slack: https://{YOUR_ORG}.slack.com/archives/C12345/p1234567890
```

## Advanced: Custom Integrations

### Extend to Additional Systems

Edit the skill to add:
- **Email**: Send minutes to distribution list
- **Confluence**: Update meeting notes page
- **Azure DevOps**: Create work items
- **Asana**: Create tasks
- **Notion**: Add to meeting database

## Troubleshooting

### Q: Transcript quality is poor (bad speaker IDs)

**A**: Provide speaker list upfront:
```
agent: "Process transcript (speakers: Sarah, John, Alice, Mike)"
```

### Q: Missing key action/decision

**A**: Agent's detection uses heuristics. You can:
1. Manually add to minutes before posting
2. Increase `decision_confidence_threshold` in config
3. Ask agent to re-process with specific guidance

### Q: Too many false-positive actions

**A**: Agent is being overly aggressive. Adjust config:
```yaml
action_clarity_threshold: 0.7  # Higher = stricter
decision_confidence_threshold: 0.7
```

### Q: Want to review before posting to GitHub/Jira

**A**: Use interactive prompts:
```bash
agent: "Process meeting, show me markdown first"
```

Agent will display minutes and ask for confirmation before posting.

## Tips & Best Practices

1. **Speaker Identification**: Clear, consistent speaker names help accuracy
2. **Explicit Actions**: Say "Owner: John" for clearer action assignment
3. **Deadlines**: Mention "by Friday" or "next Monday" for due dates
4. **Decisions**: Use clear language: "we decided", "we agreed", "approved"
5. **Blockers**: Explicitly state blockers: "blocked by X", "waiting for Y"

## Related Integrations

- `github-cli` — Post to GitHub issues
- `jira-api` — Create Jira tickets
- `slack-api` — Post to Slack channels
- `markdown` — Format output

## Notes

- Transcripts are not sent to external APIs (processed locally)
- GitHub/Jira/Slack require valid API keys in ~/.config/
- Config file loads from `~/.config/meeting-notes/config.yaml`
- Minutes are saved to `~/meeting-minutes/` by default

---

**Created**: 2025-03-11  
**Author**: contributors  
**Version**: 1.0  
**License**: MIT

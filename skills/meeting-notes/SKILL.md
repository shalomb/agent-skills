---
name: meeting-notes
description: Process meeting transcripts (VTT format) to extract meeting minutes, action items, and decisions. Use when given transcript files or asked to create meeting documentation, extract action items, or record decisions.
---

# Meeting Notes Skill

Process Microsoft Teams meeting transcripts (VTT format) to extract meeting minutes, action items, and decisions.

## Task Flow

1. **Transcript Parsing**: Read VTT (WebVTT) format files. See [references/formats.md](references/formats.md) for parsing logic.
2. **Analysis**: Identify decisions, actions, and key discussions using NLP and pattern matching.
3. **Generation**: Produce structured markdown meeting minutes. See [references/examples.md](references/examples.md) for standard output format.
4. **Integration**: Offer to update GitHub issues, Jira tickets, or Slack messages.

## Output Structure

The primary output is markdown minutes containing:
- **Meeting Header** (title, date, attendees, duration)
- **Executive Summary** (1-2 sentence overview)
- **Decisions** (bulleted list with rationale and owners)
- **Action Items** (table format with owner, description, and due date)
- **Key Discussion Points** (organized by topic)
- **Blockers & Follow-ups** (open questions, escalations)

## Reference Materials

- **Formats & Logic**: [references/formats.md](references/formats.md) - VTT format details, parsing logic, and system integration commands.
- **Examples**: [references/examples.md](references/examples.md) - Comprehensive before-and-after demonstration of a meeting processing workflow.

## Features

- **Automatic Detection**: Identify speakers, decisions ("we agreed"), and actions ("@owner will").
- **Confidence Scoring**: Heuristic-based scoring for decision certainty and action clarity.
- **System Integration**: Automated `gh issue comment`, `jira issue create`, and `slack chat postMessage`.

## Related Skills & Tools

- `github-cli` - For posting to GitHub issues
- `jira` - For creating Jira tickets
- `slack-api` - For posting to Slack channels
- `markdown` - For formatting output

## Troubleshooting

- **Poor Transcript Quality**: Manually provide speaker list in the first line of the VTT.
- **False-Positives**: Use the summary prompt to manually filter incorrect actions before integration.
- **Large Meetings**: Be concise in discussion summaries to avoid context bloat.

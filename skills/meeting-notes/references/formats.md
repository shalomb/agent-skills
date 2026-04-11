# Meeting Notes Formats

This reference documents the input formats and interactive patterns used by the meeting-notes skill.

## VTT File Format (Teams Transcript)

Standard WebVTT format as exported by Microsoft Teams.

```vtt
WEBVTT

00:00:01.000 --> 00:00:05.000
Speaker: Hello, this is the architecture review meeting

00:00:05.100 --> 00:00:10.500
Speaker: We need to decide on the database design

00:00:10.600 --> 00:00:15.200
Other Speaker: I think PostgreSQL is the right choice
```

### Parsing Logic
- **Timestamps**: `00:00:01.000` format
- **Speaker name**: Text before the colon
- **Content**: Text after the colon

## Interactive Prompts

After processing a transcript, the agent should present a summary and offer integration options.

### Summary Example
```
I've processed the transcript and extracted:
- 3 decisions (PostgreSQL selected, 2 others)
- 5 action items (owners: @alice, @bob, @charlie)
- 2 blockers (need X approval, waiting for Y data)
```

### Selection Menu
```
What would you like to do?

1. [ ] Post as GitHub comment on issue #123
2. [ ] Create Jira ticket for tracking
3. [ ] Update Slack thread
4. [ ] Save minutes to file (minutes-2025-03-11.md)
5. [ ] All of the above
```

## System Integrations

### GitHub
```bash
gh issue comment {issue_number} --body "{formatted_minutes}"
```

### Jira
```bash
jira issue create --parent {key} --type Subtask --summary "{action_item}"
```

### Slack
```bash
slack chat postMessage --channel {channel} --text "{summary}"
```

# Prompt: Extract Meeting Minutes from Teams Transcript

**Purpose**: Parse VTT transcript and extract structured meeting minutes with decisions, actions, and follow-ups.

**Target Model**: Claude 3.5 Sonnet (required for NLP analysis)

**Input**: WebVTT transcript file content

**Output**: Structured JSON + Markdown minutes

---

## Task

You are a meeting minutes expert. Your job is to read a Teams meeting transcript (VTT format) and extract:

1. **Meeting Metadata**: Title, date, attendees, duration
2. **Decisions**: What was decided, by whom, confidence level
3. **Action Items**: Owner, what needs to be done, due date/timeline
4. **Follow-ups**: Blockers, questions, escalations
5. **Discussion Summary**: Key points discussed by topic
6. **Participant Stats**: Who spoke, how much

## Input Format

VTT (WebVTT) transcript with timestamps and speaker names:

```
WEBVTT

HH:MM:SS.mmm --> HH:MM:SS.mmm
Speaker Name: Content of what they said

HH:MM:SS.mmm --> HH:MM:SS.mmm
Other Speaker: More content
```

## Processing Instructions

### Step 1: Parse Transcript Metadata

Extract:
- **Meeting Title**: Infer from first few speaker turns or context
- **Date**: Extract from file metadata or context (YYYY-MM-DD)
- **Attendees**: List unique speaker names
- **Duration**: Calculate from first to last timestamp
- **Language**: Detected language

Example output:
```json
{
  "metadata": {
    "title": "ChemDraw Architecture Review",
    "date": "2025-03-11",
    "attendees": ["Sarah", "John", "Alice"],
    "duration_minutes": 90,
    "language": "en"
  }
}
```

### Step 2: Extract Decisions

**Look for language patterns**:
- "We decided..."
- "We agreed..."
- "Let's go with..."
- "I move that..."
- "Unanimous decision..."
- "[Person] will..."
- "Approved: ..."

**For each decision, capture**:
- Decision statement (1-2 sentences)
- Context: Why this decision? What alternatives considered?
- Owner: Who is driving this?
- Confidence: HIGH/MEDIUM/LOW based on clarity and consensus
- Timestamp: When was it decided?

Example output:
```json
{
  "decisions": [
    {
      "id": "D1",
      "statement": "Use PostgreSQL as primary database for GxP system",
      "context": "Chosen for JSON support, GxP compliance track record, mature ecosystem",
      "owner": "John",
      "confidence": "HIGH",
      "timestamp": "00:00:20",
      "alternatives_considered": ["MySQL", "Oracle"]
    }
  ]
}
```

### Step 3: Extract Action Items

**Look for language patterns**:
- "I need to..."
- "Can you..."
- "Follow up on..."
- "Action item: ..."
- "Owner: [Name]"
- "By [date/timeline]"

**For each action, capture**:
- Action description (what needs to be done?)
- Owner (who is responsible?)
- Due date or timeline (when?)
- Priority: CRITICAL/HIGH/MEDIUM/LOW
- Clarity: HIGH/MEDIUM/LOW (is it specific enough?)
- Status: Not Started / In Progress / Blocked / Done

Example output:
```json
{
  "action_items": [
    {
      "id": "A1",
      "description": "Document PostgreSQL design rationale and schema",
      "owner": "John",
      "due_date": "2025-03-14",
      "due_timeline": "Friday",
      "priority": "HIGH",
      "clarity": "HIGH",
      "status": "Not Started",
      "timestamp": "00:00:30"
    },
    {
      "id": "A2",
      "description": "Get security team approval for encryption approach",
      "owner": "Alice",
      "due_date": "2025-03-17",
      "due_timeline": "Monday",
      "priority": "CRITICAL",
      "clarity": "HIGH",
      "status": "Blocked",
      "blocker": "Awaiting security team input",
      "timestamp": "00:00:45"
    }
  ]
}
```

### Step 4: Extract Follow-ups

**Look for language patterns**:
- "We need to..."
- "Let's follow up..."
- "I'm blocked by..."
- "Waiting for..."
- "Question: ..."
- "Unclear: ..."

**Categories**:
- **Blocker**: Something blocking progress
- **Question**: Unanswered question
- **Escalation**: Needs higher-level decision/approval
- **Dependency**: Depends on external work
- **Clarification**: Needs follow-up clarification

Example output:
```json
{
  "follow_ups": [
    {
      "id": "F1",
      "type": "blocker",
      "description": "Security team approval needed for encryption approach",
      "owner": "Alice",
      "due": "Monday",
      "impact": "Blocks schema design and implementation"
    },
    {
      "id": "F2",
      "type": "question",
      "description": "Which PostgreSQL version supports GxP environments best?",
      "owner": "John",
      "due": "Friday"
    }
  ]
}
```

### Step 5: Group Discussion by Topic

**Look for natural breaks in conversation**:
- Topic transitions (e.g., "Let's move to..." or natural pause)
- Subtopic groupings within main discussion
- Decision points mark topic boundaries

**For each topic, capture**:
- Topic name
- Participants (who spoke about this?)
- Key points (bullet list)
- Decisions made in this section
- Actions assigned in this section
- Duration (approx timestamps)

Example output:
```json
{
  "discussion_topics": [
    {
      "topic": "Database Design Rationale",
      "participants": ["John", "Sarah"],
      "duration_start": "00:00:10",
      "duration_end": "00:00:35",
      "key_points": [
        "PostgreSQL chosen for JSON support",
        "GxP compliance is critical",
        "Mature ecosystem reduces risk"
      ],
      "decisions_in_section": ["D1"],
      "actions_in_section": ["A1"]
    }
  ]
}
```

### Step 6: Calculate Participant Statistics

**For each speaker, calculate**:
- Total speaking turns
- Total words spoken (approximate)
- Percentage of speaking time
- Primary role (facilitator, decision-maker, stakeholder, etc.)
- Key contributions (decisions made, actions owned, questions asked)

Example output:
```json
{
  "participants": [
    {
      "name": "Sarah",
      "speaking_turns": 5,
      "estimated_words": 450,
      "percentage_of_time": "45%",
      "role": "Facilitator",
      "decisions_owned": 0,
      "actions_owned": 1,
      "questions_asked": 2
    },
    {
      "name": "John",
      "speaking_turns": 4,
      "estimated_words": 380,
      "percentage_of_time": "38%",
      "role": "Decision Maker",
      "decisions_owned": 1,
      "actions_owned": 2,
      "questions_asked": 0
    }
  ]
}
```

### Step 7: Generate Executive Summary

**Write a 1-2 sentence summary** that captures:
- What was the main purpose of the meeting?
- What was the primary outcome/decision?
- Any critical blockers or follow-ups?

Example:
```
Team decided on PostgreSQL as the primary database for the ChemDraw GxP system,
prioritizing JSON support and regulatory compliance. One critical blocker identified:
security team approval needed for encryption approach by Monday.
```

---

## Output Format

Generate **both**:

1. **Structured JSON** (for programmatic use):
```json
{
  "metadata": { ... },
  "executive_summary": "...",
  "decisions": [ ... ],
  "action_items": [ ... ],
  "follow_ups": [ ... ],
  "discussion_topics": [ ... ],
  "participants": [ ... ]
}
```

2. **Formatted Markdown** (for human reading):
```markdown
# Meeting Minutes: {Title}

**Date**: {Date}
**Duration**: {Duration}
**Attendees**: {List}

## Executive Summary
{Summary}

## Decisions
[Formatted list with owners and confidence]

## Action Items
[Formatted as table with owner/description/due]

## Key Discussion Points
[By topic, with key points]

## Blockers & Follow-ups
[Categorized by type]

## Participants
[With stats on speaking time]
```

---

## Confidence Scoring

### Decision Confidence
- **HIGH**: Clear agreement, explicit language ("we decided", "approved")
- **MEDIUM**: Implied decision, some discussion but no clear dissent
- **LOW**: Tentative decision, ongoing debate, conditional approval

### Action Clarity
- **HIGH**: Clear owner, specific deliverable, concrete deadline
- **MEDIUM**: Owner identified but vague deliverable or timeline
- **LOW**: Unclear owner, vague action, no deadline

### Discussion Relevance
- **HIGH**: Directly influences decisions or actions
- **MEDIUM**: Provides useful context
- **LOW**: Tangential or informational

---

## Error Handling

**If speaker name unclear**:
- Use [Speaker 1], [Speaker 2], etc.
- Flag in output: `speaker_identification: UNCLEAR`

**If no clear decisions made**:
- Note: `decisions_found: 0`
- Output what was discussed instead

**If no actions assigned**:
- Flag: `action_items_found: 0`
- Summarize what needs follow-up

**If transcript is incomplete**:
- Process what's available
- Flag: `transcript_completeness: PARTIAL`

---

## Example Input & Output

### Input (VTT)
```
WEBVTT

00:00:15.200 --> 00:00:20.100
Sarah: Welcome to the ChemDraw architecture review. Today we're deciding on the database design.

00:00:20.200 --> 00:00:25.500
John: I think PostgreSQL is the best choice because of JSON support and GxP compliance.

00:00:25.600 --> 00:00:30.200
Sarah: We agreed on PostgreSQL. John, can you document the rationale by Friday?

00:00:30.300 --> 00:00:35.100
John: Yes, I'll have that ready by Friday.

00:00:35.200 --> 00:00:40.600
Alice: I have a blocker - we need security team approval for the encryption approach.

00:00:40.700 --> 00:00:45.300
Sarah: Alice, can you reach out to security? Let's follow up Monday.
```

### Output (JSON)
```json
{
  "metadata": {
    "title": "ChemDraw Architecture Review",
    "date": "2025-03-11",
    "attendees": ["Sarah", "John", "Alice"],
    "duration_minutes": 1,
    "speaker_identification": "CLEAR"
  },
  "executive_summary": "Team decided on PostgreSQL for ChemDraw GxP database. One blocker: security approval needed for encryption approach.",
  "decisions": [
    {
      "id": "D1",
      "statement": "Use PostgreSQL as database for GxP system",
      "owner": "John",
      "confidence": "HIGH",
      "timestamp": "00:00:20"
    }
  ],
  "action_items": [
    {
      "id": "A1",
      "description": "Document PostgreSQL design rationale",
      "owner": "John",
      "due_date": "2025-03-14",
      "priority": "HIGH",
      "clarity": "HIGH",
      "status": "Not Started"
    },
    {
      "id": "A2",
      "description": "Get security team approval for encryption",
      "owner": "Alice",
      "due_date": "2025-03-17",
      "priority": "CRITICAL",
      "clarity": "HIGH",
      "status": "Blocked"
    }
  ]
}
```

---

**Model Recommendation**: Claude 3.5 Sonnet (best at NLP + JSON generation)
**Processing Time**: ~30-60 seconds per hour of transcript
**Max Input**: 100k tokens (~8 hours of transcript)

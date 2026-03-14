# Teams Transcript Processor: Example

Complete example showing VTT input → extracted minutes → system integrations.

## Example 1: ChemDraw Architecture Meeting

### Input: Meeting Transcript (example.vtt)

```vtt
WEBVTT

00:00:15.200 --> 00:00:20.100
Sarah: Welcome to the ChemDraw architecture review meeting. Today we're finalizing the database design decision.

00:00:20.200 --> 00:00:25.500
John: I've done some analysis. I think PostgreSQL is the best choice for us. We get JSON support, GxP compliance track record, and mature tooling.

00:00:25.600 --> 00:00:30.200
Sarah: Those are good points. Does anyone have concerns with PostgreSQL?

00:00:30.300 --> 00:00:35.100
Alice: I don't have concerns about PostgreSQL itself, but we need to address the encryption approach before we can move forward.

00:00:35.200 --> 00:00:40.600
John: Good point. The encryption is a security question that needs formal review.

00:00:40.700 --> 00:00:45.300
Sarah: So we're agreed on PostgreSQL. John, can you write up the rationale and design by Friday? And Alice, can you reach out to the security team about the encryption approach?

00:00:45.400 --> 00:00:50.200
Alice: Yes, I'll get that started. Should have initial feedback by Monday.

00:00:50.300 --> 00:00:55.700
John: I'll also document the schema design. We should aim to finalize the schema after security review.

00:00:55.800 --> 00:01:00.500
Sarah: Perfect. Let's plan a follow-up sync for Monday next week to review encryption feedback and finalize the schema.

00:01:00.600 --> 00:01:05.200
Mike: Before we close out, should we consider RTO/RPO for the database? That might impact the architecture.

00:01:05.300 --> 00:01:10.100
Sarah: Great question. Mike, can you investigate backup and recovery options? We'll discuss at the next meeting.

00:01:10.200 --> 00:01:15.600
Mike: Sure, I'll put together options for Monday's sync.

00:01:15.700 --> 00:01:20.300
Sarah: Excellent. So to recap: PostgreSQL is decided, John documents design, Alice gets security approval, Mike investigates backup options. We sync Monday.
```

### Output 1: Extracted JSON

```json
{
  "metadata": {
    "title": "ChemDraw Architecture Review",
    "date": "2025-03-11",
    "attendees": ["Sarah", "John", "Alice", "Mike"],
    "duration_minutes": 5,
    "speaker_identification": "CLEAR",
    "timestamp_range": "00:00:15 - 00:01:20"
  },
  "executive_summary": "Team decided on PostgreSQL as primary database for ChemDraw GxP system. Critical blocker: security team approval needed for encryption approach by Monday. Follow-up meeting scheduled for Monday to review encryption feedback and finalize schema.",
  "decisions": [
    {
      "id": "D1",
      "statement": "PostgreSQL selected as primary database engine",
      "context": "Chosen for JSON support, GxP compliance track record, mature tooling ecosystem",
      "owner": "John",
      "confidence": "HIGH",
      "timestamp": "00:00:20",
      "alternatives_considered": ["MySQL", "Oracle"],
      "rationale": "JSON support enables flexible schema. GxP compliance history reduces regulatory risk. Mature tooling reduces technical debt."
    }
  ],
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
      "timestamp": "00:00:45",
      "notes": "Needs to include schema design and configuration options"
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
      "timestamp": "00:00:45",
      "blocker": "Awaiting security team formal review",
      "impact": "Blocks schema finalization and implementation phase"
    },
    {
      "id": "A3",
      "description": "Investigate backup and recovery options (RTO/RPO)",
      "owner": "Mike",
      "due_date": "2025-03-17",
      "due_timeline": "Monday",
      "priority": "MEDIUM",
      "clarity": "HIGH",
      "status": "Not Started",
      "timestamp": "00:01:05",
      "notes": "Put together options for discussion at Monday sync"
    }
  ],
  "follow_ups": [
    {
      "id": "F1",
      "type": "blocker",
      "description": "Security team approval needed for encryption approach",
      "owner": "Alice",
      "due": "2025-03-17",
      "impact": "Blocks schema finalization and implementation",
      "severity": "CRITICAL"
    },
    {
      "id": "F2",
      "type": "meeting",
      "description": "Follow-up sync to review encryption feedback and finalize schema",
      "scheduled_for": "2025-03-17",
      "participants": ["Sarah", "John", "Alice", "Mike"],
      "topics": ["Encryption approval feedback", "Backup/recovery options", "Schema finalization"]
    },
    {
      "id": "F3",
      "type": "question",
      "description": "What RTO/RPO requirements should we target for the database?",
      "owner": "Mike",
      "status": "Under Investigation"
    }
  ],
  "discussion_topics": [
    {
      "topic": "PostgreSQL Selection",
      "participants": ["John", "Sarah", "Alice"],
      "duration_start": "00:00:20",
      "duration_end": "00:00:45",
      "key_points": [
        "PostgreSQL has JSON support",
        "Good GxP compliance track record",
        "Mature, well-supported ecosystem",
        "Encryption approach needs security review"
      ],
      "decisions_in_section": ["D1"],
      "actions_in_section": ["A1", "A2"]
    },
    {
      "topic": "Backup and Recovery Requirements",
      "participants": ["Mike", "Sarah"],
      "duration_start": "00:01:05",
      "duration_end": "00:01:20",
      "key_points": [
        "RTO/RPO impacts architecture decisions",
        "Should be investigated before schema finalization",
        "Options needed for Monday discussion"
      ],
      "decisions_in_section": [],
      "actions_in_section": ["A3"]
    }
  ],
  "participants": [
    {
      "name": "Sarah",
      "speaking_turns": 5,
      "estimated_words": 280,
      "percentage_of_time": "40%",
      "role": "Facilitator",
      "decisions_owned": 0,
      "actions_owned": 0,
      "questions_asked": 1
    },
    {
      "name": "John",
      "speaking_turns": 3,
      "estimated_words": 220,
      "percentage_of_time": "32%",
      "role": "Technical Lead",
      "decisions_owned": 1,
      "actions_owned": 1,
      "questions_asked": 0
    },
    {
      "name": "Alice",
      "speaking_turns": 3,
      "estimated_words": 180,
      "percentage_of_time": "17%",
      "role": "Security Owner",
      "decisions_owned": 0,
      "actions_owned": 1,
      "questions_asked": 0
    },
    {
      "name": "Mike",
      "speaking_turns": 2,
      "estimated_words": 120,
      "percentage_of_time": "11%",
      "role": "Infrastructure",
      "decisions_owned": 0,
      "actions_owned": 1,
      "questions_asked": 1
    }
  ]
}
```

### Output 2: Formatted Markdown

```markdown
# Meeting Minutes: ChemDraw Architecture Review

**Date**: March 11, 2025  
**Time**: 12:00 PM - 12:05 PM UTC  
**Duration**: 5 minutes  
**Attendees**: Sarah (Facilitator), John (Technical Lead), Alice (Security), Mike (Infrastructure)  
**Recording**: [Link to Teams Recording]

---

## Executive Summary

Team decided on **PostgreSQL** as the primary database engine for the ChemDraw GxP system, prioritizing JSON support and regulatory compliance. One critical blocker identified: security team approval needed for encryption approach by Monday. Follow-up sync scheduled for Monday to review security feedback and finalize database schema.

---

## 🎯 Decisions

### D1: PostgreSQL as Primary Database ✅

| Attribute | Value |
|-----------|-------|
| **Decision** | Use PostgreSQL as primary database engine |
| **Owner** | John |
| **Confidence** | HIGH |
| **Rationale** | JSON support for flexible schema; GxP compliance track record; mature, well-supported ecosystem |
| **Alternatives Considered** | MySQL, Oracle |
| **Implications** | Reduces regulatory risk, enables flexible data modeling, reduces technical debt |

---

## 📋 Action Items

| ID | Action | Owner | Due | Priority | Status |
|----|----|-------|-----|----------|--------|
| A1 | Document PostgreSQL design rationale and schema | John | Friday 3/14 | HIGH | Not Started |
| A2 | Get security team approval for encryption approach | Alice | Monday 3/17 | **CRITICAL** | **Blocked** 🚫 |
| A3 | Investigate backup and recovery options (RTO/RPO) | Mike | Monday 3/17 | MEDIUM | Not Started |

---

## 🚨 Blockers & Follow-ups

### Blocker: Security Approval for Encryption
- **Description**: Security team approval needed for encryption approach
- **Owner**: Alice
- **Due**: Monday, March 17
- **Impact**: Blocks schema finalization and implementation phase
- **Severity**: CRITICAL ⚠️

### Follow-up Meeting: Monday Sync
- **Date**: Monday, March 17, 2025
- **Topics**:
  - Review encryption approval feedback from security team
  - Discuss backup/recovery options (RTO/RPO)
  - Finalize database schema
- **Attendees**: Sarah, John, Alice, Mike

### Open Question
- **Q**: What RTO/RPO requirements should we target for the database?
- **Owner**: Mike (investigating)
- **Due**: Monday 3/17

---

## 💬 Key Discussion Points

### PostgreSQL Selection
- **Participants**: John, Sarah, Alice
- **Duration**: ~25 minutes

PostgreSQL selected over alternatives due to:
1. **JSON Support** — Enables flexible schema design without migrations
2. **GxP Compliance** — Proven track record in regulated environments
3. **Mature Ecosystem** — Well-supported, reduces technical debt
4. **Security Considerations** — Encryption approach needs formal security review before proceeding

### Backup and Recovery Requirements
- **Participants**: Mike, Sarah
- **Duration**: ~15 minutes

RTO (Recovery Time Objective) and RPO (Recovery Point Objective) requirements need investigation:
- Impact architecture and infrastructure costs
- Should be defined before finalizing schema
- Mike will prepare options for Monday discussion

---

## 👥 Participant Summary

| Participant | Role | Speaking Time | Contributions |
|-------------|------|---------------|----------------|
| **Sarah** | Facilitator | 40% | Led discussion, asked clarifying questions, set action items |
| **John** | Technical Lead | 32% | Proposed PostgreSQL, will document design |
| **Alice** | Security Owner | 17% | Identified security requirements, owning security approval |
| **Mike** | Infrastructure | 11% | Raised RTO/RPO consideration, investigating backup options |

---

## ✅ Next Steps

1. **John** → Document PostgreSQL design rationale by Friday (3/14)
2. **Alice** → Reach out to security team, target initial feedback by Monday (3/17)
3. **Mike** → Prepare RTO/RPO backup options by Monday (3/17)
4. **Sarah** → Schedule follow-up sync for Monday to review findings

**Follow-up Meeting**: Monday, March 17, 2025 @ [Time TBD]

---

**Minutes recorded**: 2025-03-11 12:10 PM  
**Prepared by**: Meeting Minutes Processor Bot  
**Last updated**: 2025-03-11
```

### Output 3: GitHub Issue Comment

```markdown
## 📋 Meeting Minutes: ChemDraw Architecture Review

**Date**: Mar 11, 2025 | **Duration**: 5 min | **Attendees**: Sarah, John, Alice, Mike

### ✅ Decisions Made
- **PostgreSQL** selected as primary database (HIGH confidence)
  - Rationale: JSON support, GxP compliance, mature ecosystem
  - Owner: @john (will document)

### 📝 Action Items
- @john — Document PostgreSQL design rationale & schema (📅 Friday 3/14)
- @alice — Get security team encryption approval (📅 Monday 3/17) 🚫 **BLOCKED**
- @mike — Investigate backup/recovery options (📅 Monday 3/17)

### 🚨 Blockers
- 🚫 **Critical**: Security team approval needed for encryption approach
  - Blocks: Schema finalization, implementation phase
  - Owner: @alice
  - Due: Monday 3/17

### 📅 Follow-up Meeting
Monday, March 17 — Review security feedback and finalize schema
- Topics: Encryption approval, backup options, schema finalization
- Attendees: Sarah, John, Alice, Mike

### 💡 Key Points
- PostgreSQL chosen for JSON support and regulatory compliance
- Encryption is a blocker — security review required before schema finalization
- RTO/RPO requirements need investigation to complete architecture
```

### Output 4: Jira Subtasks Created

```
Parent Issue: DAD-123 (ChemDraw Architecture Review)

Subtask 1:
- Key: DAD-123.1
- Title: Document PostgreSQL design rationale and schema
- Assignee: John Smith
- Due Date: 2025-03-14
- Priority: High
- Status: To Do
- Description: Document PostgreSQL selection rationale, schema design, configuration options. Required before security review.
- Linked issue: DAD-123

Subtask 2:
- Key: DAD-123.2
- Title: Get security team approval for encryption approach
- Assignee: Alice Johnson
- Due Date: 2025-03-17
- Priority: Critical ⚠️
- Status: Blocked
- Labels: blocker, security-review
- Description: Reach out to security team for formal encryption approach review. This is blocking schema finalization.
- Blocker: Awaiting security team feedback
- Linked issue: DAD-123

Subtask 3:
- Key: DAD-123.3
- Title: Investigate backup and recovery options (RTO/RPO)
- Assignee: Mike Chen
- Due Date: 2025-03-17
- Priority: Medium
- Status: To Do
- Description: Prepare options for database backup and recovery strategies. Should include RTO and RPO targets for different scenarios. Discuss at Monday sync.
- Linked issue: DAD-123
```

### Output 5: Slack Thread

**Main Message**:
```
📋 ChemDraw Architecture Review Summary

✅ **Decisions**: 1 (PostgreSQL selected)
📝 **Actions**: 3 assigned to team
🚫 **Blockers**: 1 critical (security approval)
⏱️ **Duration**: 5 minutes | **Attendees**: 4

---

📅 **Follow-up meeting**: Monday, March 17
```

**Thread Reply 1 — Action Items**:
```
📋 **Action Items**

@john — Document PostgreSQL design by Friday 3/14
@alice — Get security team approval by Monday 3/17 🚫 **BLOCKED**
@mike — Investigate backup/recovery options by Monday 3/17

[Links to GitHub issue #456 and Jira DAD-123]
```

**Thread Reply 2 — Decisions**:
```
✅ **Decision: PostgreSQL as Primary Database**

Rationale:
• JSON support for flexible schema
• GxP compliance proven track record
• Mature, well-supported ecosystem

Owner: @john (will document)
```

**Thread Reply 3 — Blockers**:
```
🚫 **Critical Blocker**

Security team approval needed for encryption approach
• Owner: @alice
• Due: Monday 3/17
• Impact: Blocks schema finalization
• Action: Reach out to security for formal review
```

---

## Example 2: Quick Usage

### Scenario: User Processes Transcript

```bash
Agent: "Process my architecture meeting transcript from yesterday"

User provides: meeting-transcript.vtt

Agent processes and asks:
──────────────────────

I've processed your ChemDraw architecture meeting:

✅ 1 decision made (PostgreSQL)
✅ 3 action items assigned
✅ 1 critical blocker identified
✅ 2 follow-up topics identified

What would you like to do?

1. [ ] Post minutes to GitHub issue #456
2. [ ] Create Jira subtasks for action items
3. [ ] Post summary to Slack #architecture
4. [ ] Save minutes to file
5. [ ] All of the above
6. [ ] Show me the markdown first

Enter selections (1,2,3,4,5) or press Enter:
```

### User Response: "1,2,3,4"

```bash
Agent executes:

⏳ Posting to GitHub issue #456...
✅ Posted comment with minutes and action items

⏳ Creating 3 Jira subtasks...
✅ Created DAD-123.1 (John's task)
✅ Created DAD-123.2 (Alice's task)
✅ Created DAD-123.3 (Mike's task)

⏳ Posting to Slack #architecture...
✅ Posted summary message with thread replies

⏳ Saving to file...
✅ Saved to ~/shalomb/meeting-minutes/minutes-2025-03-11-chemdraw-architecture.md

───────────────────────

📊 Summary:
• GitHub issue #456 updated
• 3 Jira subtasks created (DAD-123.1, DAD-123.2, DAD-123.3)
• Slack thread posted to #architecture
• Minutes saved locally

🔗 Quick Links:
• GitHub: https://github.com/oneTakeda/...#comment-12345
• Jira: https://takeda.atlassian.net/browse/DAD-123
• Slack: https://takeda.slack.com/archives/C.../p123456
```

---

**Generated**: 2025-03-11  
**Example Type**: Complete workflow with all integrations

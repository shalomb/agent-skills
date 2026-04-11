# Meeting Notes Examples

This reference provides comprehensive examples of processing meeting transcripts.

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
```

### Agent Output

```markdown
# Meeting Minutes: ChemDraw Architecture Review

**Date**: 2025-03-11  
**Attendees**: Sarah (host), John, Alice  

## Executive Summary
Team decided on PostgreSQL as database engine for ChemDraw GxP system, prioritizing JSON support and regulatory compliance.

## Decisions

1. **Database Engine: PostgreSQL** ✅
   - Rationale: JSON support, GxP compliance, mature ecosystem
   - Owner: John
   
## Action Items

| Owner | Action | Due Date | Status |
|-------|--------|----------|--------|
| John | Document PostgreSQL rationale & design | 2025-03-14 (Fri) | Not Started |
| Alice | Get security team approval for encryption | 2025-03-17 (Mon) | Blocked |

## Key Discussion Points

### Database Design Rationale
- PostgreSQL chosen over MySQL due to:
  - Native JSON/JSONB support
  - GxP compliance track record
  - Mature tooling ecosystem
```

### Agent Prompt to User

```
I've extracted the following from your ChemDraw architecture meeting:

✅ 2 decisions (PostgreSQL, encryption approach TBD)
✅ 3 action items (John, Alice, Sarah)
✅ 1 blocker (security approval needed)

What would you like to do?

1. [ ] Post minutes to GitHub issue #456 (ChemDraw Architecture)
2. [ ] Create Jira subtasks for action items
3. [ ] Update Slack #architecture channel
4. [ ] Save to file (minutes-2025-03-11-architecture-review.md)
```

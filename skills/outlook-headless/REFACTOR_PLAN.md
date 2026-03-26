# Intent: Robust Outlook Conversation Extraction

This document outlines the plan to refactor the `outlook-headless` skill to support reliable extraction of multi-message conversation threads, addressing bugs identified during the "Simca Online Server" extraction task.

## Identified Issues
1. **Partial Extraction**: Only 1-2 messages were captured from a 9-message thread.
2. **Expansion Failure**: Clicking collapsed headers (`aria-expanded="false"`) sometimes toggled them closed or caused the reading pane to reset.
3. **Sender Misattribution**: All messages in a thread were often attributed to the same sender.
4. **Invalid Selectors**: Use of Playwright-specific pseudo-selectors inside `page.evaluate`.
5. **Performance**: Structure-heavy extraction is too slow for large threads.

## Refactor Goals (BDD/TDD)

### 1. Reliable Thread Expansion (BDD)
- **Feature**: `features/conversation_expansion.feature`
- **Goal**: Ensure that "9 messages" and "Show more" buttons are clicked before extraction begins.
- **Success Criteria**: `doc_count` in the reading pane matches the expected thread size.

### 2. Contextual Message Parsing (TDD)
- **Test**: `tests/test_parser.py` (updated) and new `tests/test_thread_extraction.py`
- **Goal**: Associate each `role="document"` with its specific header (Sender/Timestamp).
- **Success Criteria**: Each message in the resulting JSON has its own correct sender and timestamp.

### 3. Robust Selectors & Fallbacks (TDD)
- **Goal**: Replace non-standard JS selectors and add fallbacks for message bodies.
- **Success Criteria**: Extraction works even when `role="document"` is missing (e.g., in drafts).

### 4. Fast Raw Dump Mode (BDD)
- **Feature**: `features/raw_dump.py`
- **Goal**: Provide a `--raw` flag to quickly capture the entire reading pane HTML.
- **Success Criteria**: Immediate capture of thread text without per-message parsing overhead.

## Execution Order
1. Define Gherkin scenarios for expansion.
2. Update `models.py` if needed to support nested threads or better metadata.
3. Implement failing tests for header association.
4. Refactor `outlook_client.py` and `parser.py` iteratively.
5. Verify against the "Simca Online Server" thread.

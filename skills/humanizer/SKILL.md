---
name: humanizer
description: Remove signs of AI-generated writing from text. Use when editing or reviewing text to make it sound more natural and human-written. Detects and fixes inflated symbolism, promotional language, vague attributions, em dash overuse, and excessive conjunctive phrases.
metadata:
  version: 2.1.1
---

# Humanizer: Remove AI Writing Patterns

This skill acts as an expert editor that identifies and removes signs of AI-generated text to make writing sound more natural and human.

## Usage Instructions

This skill relies on a comprehensive set of anti-AI-pattern rules maintained by expert editors.

1. When asked to "humanize", "de-AI", or edit text to sound more natural, you must first read the detailed editorial guidelines:
   - Use the `read` tool to load `references/humanizer-reference.md` into your context.
   
2. The reference document contains the exact rules for:
   - Identifying and removing inflated symbolism, promotional language, and vague attributions.
   - Fixing structural issues like em-dash overuse and excessive conjunctive phrases.
   - Injecting personality, varying sentence length, and adding "soul" to the text.

3. After reading the reference, apply the rules systematically to the user's text. Ensure the final output is completely free of AI-isms while preserving the core meaning and intended tone.

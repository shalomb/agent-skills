---
name: ai-text-humanizer
description: |
  Use this skill to identify and remove signs of AI-generated writing from text.
  Trigger this whenever asked to review, edit, or "humanize" a document to make
  it sound more natural, professional, and less like a chatbot. Essential for
  refining Architecture Decision Records (ADRs), policy documents, and executive
  communications by eliminating promotional language, filler, and repetitive patterns.
  Must always apply.
---

# Humanizer: Remove AI Writing Patterns

Edit text to remove AI patterns and add human voice. This guide combines Wikipedia's "Signs of AI writing" with strict technical documentation standards to produce clean, natural prose.

## Process

1. **Scan for patterns** - Check against the anti-patterns in [references/patterns.md](references/patterns.md).
2. **Rewrite** - Preserve meaning and match the intended tone while applying the rules.
3. **Add soul** - See the section below.
4. **Self-audit** - Ask: "What makes this obviously AI generated?" Fix any remaining tells.

## Adding soul

Avoiding AI patterns is only half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made. Tangents and half-formed thoughts are human.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

## Reference Materials

- **AI Patterns**: [references/patterns.md](references/patterns.md) - The definitive list of 32 AI writing tells, spanning content, style, filler, and jargon.
- **Examples**: [references/examples.md](references/examples.md) - Before-and-after demonstrations of the humanization process.

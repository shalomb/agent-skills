# Model Spread Heuristics

## Available models (verified working)

| Model | Via | Context | Speed | Best for |
|---|---|---|---|---|
| `anthropic/claude-haiku-4-5` | `pi --models` | 200K | Fast | Focused feature work, new API/CLI, task list execution |
| `gemini-3-flash-preview` | `gemini -y --model` | Large | Fast | Structural refactors, adversarial review, large file surgery |
| `anthropic/claude-sonnet-4-5` | `pi --models` | 200K | Medium | Complex reasoning, architecture decisions |
| `gemini-2.5-flash` | `gemini -y --model` | Large | Fast | Fallback if gemini-3-flash-preview unavailable |

## Assignment heuristics

**Use haiku (pi) when:**
- Task is a focused, well-scoped feature (new API method + CLI command)
- Task list is clear and bounded
- Many small independent tasks (burns through a TODO list efficiently)
- You want reliable tool use with predictable behaviour

**Use gemini-3-flash-preview when:**
- Large file surgery (splitting a 900-line module)
- Adversarial review (Bart) — gemini's critical nature suits this well
- You want a second opinion alongside haiku results
- The task requires reading many large files simultaneously

**Always use gemini for Bart:**
Gemini's tendency toward skepticism and thoroughness makes it naturally suited
for adversarial review. It will find issues haiku might rationalise away.

## Rate limit management

Spread across models to avoid hitting rate limits during parallel waves:
- Don't run 5 haiku agents simultaneously if you can mix 3 haiku + 2 gemini
- Wave 0 (quick wins): haiku only — fast, cheap
- Wave 1 (parallel features): mix — e.g. 2 haiku + 2 gemini
- Bart reviews: all gemini — consistent adversarial quality

## Consistency rule

If Ralph used haiku and Bart rejects → re-run Ralph with haiku.
If Ralph used gemini and Bart rejects → re-run Ralph with gemini.
Same model = same context assumptions = easier to reason about what changed.

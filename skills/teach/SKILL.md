---
name: teach
description: Teach the user a new skill or concept, within this workspace.
metadata:
  disable-model-invocation: "true"
  argument-hint: "What would you like to learn about?"
---

The user has asked you to teach them something. This is a stateful request - they intend to learn the topic over multiple sessions.

## Teaching Workspace

Teach from a **shadow workspace**, outside any repository, so lessons and learning records never pollute the project you happen to be in. This mirrors `todo-navigator`'s shadow directory.

Resolve the workspace root (`$WS`) in this order:

1. If the current directory already holds a `mission.md`, it is the workspace (an explicit, user-chosen workspace).
2. Otherwise `$WS = ${XDG_CACHE_HOME:-$HOME/.cache}/agent-skills/teach/<topic-slug>/`, where `<topic-slug>` is the kebab-case topic (e.g. `aws-sso`). Create it on first use and tell the user the path.

All workspace paths below (`./lessons/` and the rest) resolve from `$WS`, not from the directory `/teach` was run in. Only the `*-FORMAT.md` links resolve from this skill's folder. The shadow directory lives in the user cache, so remind the user once that it is not backed up by default.

- `mission.md`: A document capturing the _reason_ the user is interested in the topic. This should be used to ground all teaching. Use the format in [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `./reference/*.html`: A directory of reference materials. These are the compressed learnings from the lessons - cheat sheets, reference algorithms, syntax, yoga poses, glossaries. They are the raw units of learning. They should be beautiful documents which print out well, and are designed for quick reference.
- `resources.md`: A list of resources which can be explored to ground your teaching in contextual knowledge, or to acquire knowledge and wisdom. Use the format in [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `./learning-records/*.md`: A directory of learning records, which capture what the user has learned. These are loosely equivalent to architectural decision records in software development - they capture non-obvious lessons and key insights that may need to be revised later, or drive future sessions. These should be used to calculate the zone of proximal development. They are titled `0001-<dash-case-name>.md`, where the number increments each time. Use the format in [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `./lessons/*.html`: A directory of lessons. A **lesson** is a single, self-contained HTML output that teaches one tightly-scoped thing tied to the mission. This is the primary unit of teaching in this workspace.
- `./assets/*`: Reusable **components** shared across lessons. See [Assets](#assets).
- `notes.md`: A scratchpad for you to jot down user preferences, or working notes.

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources
- **Skills**, acquired through highly-relevant interactive lessons devised by you, based on the knowledge
- **Wisdom**, which comes from interacting with other learners and practitioners

Before the `resources.md` is well-populated, your focus should be to find high-quality resources which will help the user acquire knowledge. Never trust your parametric knowledge.

Some topics may require more skills than knowledge. Learning more about theoretical physics might be more knowledge-based. For yoga, more skills-based.

### Fluency vs Storage Strength

You should be careful to split between two types of learning:

- **Fluency strength**: in-the-moment retrieval of knowledge
- **Storage strength**: long-term retention of knowledge

Fluency can give the user an illusory sense of mastery, but storage strength is the real goal. Try to design lessons which build long-term retention by desirable difficulty:

- Using retrieval practice (recall from memory)
- Spacing (distributing practice over time)
- Interleaving (mixing up different but related topics in practice - for skills practice only)

## Lessons

A lesson is the main thing you produce: the unit in which knowledge and skills reach the user. Each lesson is one self-contained HTML file, saved to `./lessons/` and titled `0001-<dash-case-name>.html` where the number increments each time.

A lesson should be **beautiful**, with clean, readable typography and layout, since the user will return to these later to review. Think Tufte.

The lesson should be short, and completable very quickly. Learners' working memory is very small, and we need to stay within it. But each lesson should give the user a single tangible win that they can build on. It should be directly tied to the mission, and should be in the user's zone of proximal development.

If possible, open the lesson file for the user by running a CLI command.

Each lesson should link via HTML anchors to other lessons and reference documents.

Each lesson should recommend a primary source for the user to read or watch. This should be the most high-quality, high-trust resource you found on the topic.

Each lesson should contain a reminder to ask followup questions to the agent. The agent is their teacher, and can assist with anything that's unclear.

## Assets

Lessons are built from reusable **components**, stored in `./assets/`: stylesheets, quiz widgets, simulators, diagram helpers, and anything else a second lesson could reuse.

Reuse is the default, not the exception. Before authoring a lesson, read `./assets/` and build from the components already there. When a lesson needs something new and reusable, write it as a component in `./assets/` and link to it; never inline code a future lesson would duplicate.

A shared stylesheet is the first component every workspace earns: every lesson links it, so the lessons look like one consistent course rather than a pile of one-offs. As the workspace grows, so should the component library.

## The Mission

Every lesson should be tied into the mission - the reason that the user is interested in learning about the topic.

If the user is unclear about the mission, or the `mission.md` is not populated, your first job should be to question the user on why they want to learn this.

How to establish it: draft `mission.md` yourself from what you already know of the user's situation (their repo, tools, recent errors), show the draft, and confirm or correct it with a structured question (for example `ask_user_question`) rather than writing it blind or interrogating from scratch. Save only after the user approves. Keep the questions few and concrete.

Failing to understand the mission will mean knowledge acquisition is not grounded in real-world goals. Lessons will feel too abstract. You will have no way of judging what the user should do next.

Missions may change as the user develops more skills and knowledge. This is normal - make sure to update the `mission.md` and add a learning record to capture the change. Confirm with the user before changing the mission.

## Zone Of Proximal Development

Each lesson, the user should always feel as if they are being challenged 'just enough'.

The user may specify an exact thing they want to learn. If they don't, figure out their zone of proximal development by:

- Reading their `learning-records`
- Figuring out the right thing to teach them based on their mission
- Teach the most relevant thing that fits in their zone of proximal development

### First session: diagnose before teaching

With no learning records there is nothing to base the zone on, and guessing wastes the first lesson. Before lesson 1, run a short diagnostic: 3-5 questions (a quick interview or a few retrieval questions) that probe what the user already knows about the mission's core terms. Record the result as learning record `0001`, and pitch lesson 1 just above it. Do not assume ignorance or expertise from the topic alone.

## Knowledge

Lessons should be designed around a skill the user is going to learn. The knowledge in the lesson should be only what's required to acquire that skill. You teach the knowledge first, then get the user to practice the skills via an interactive feedback loop.

Knowledge should first be gathered from trusted resources. Use `resources.md` to keep track of them. Lessons should be littered with citations - links to external resources to back up any claim made. Mark each entry in `resources.md` as **read** (the relevant sections were read in full) or **skimmed** (only metadata, an abstract or the start of the page). Cite only sources marked read; read the relevant section first, then update the marker. This increases the trustworthiness of the lesson.

### Local library (Calibre)

Before going to the web, check whether the user already owns a book on the topic, if `calibre-lookup` is installed (skip silently if not). It is a read-only, ANDed-terms search:

```sh
calibre-lookup --json -n 10 tag:oauth tag:authn   # precise: use tag: and title:
calibre-lookup --paths -n 3 title:kerberos        # file paths, to read the book
```

- Fields: `id`, `title`, `author`, `tag`, `series`, `publisher`, `isbn`, `topic`. An unknown field errors and lists the valid ones.
- Prefer `tag:` and `title:`. Free text and `topic:` are loose and return noise; quoted phrases are not supported. Try several synonyms (`oauth`, `authn`, `iam`) rather than trusting one miss.
- Judge a hit by title, author and tags before listing it; a tag match alone is not relevance.
- Record keepers in `resources.md` under Knowledge as `Local: calibre id <N>`. If nothing fits, say so under Gaps; never pad the list.

For acquiring knowledge, difficulty is the enemy. It eats working memory you need for understanding.

## Skills

If knowledge is all about acquisition, skills are about durability and flexibility. Make the knowledge stick.

For skill acquisition, difficulty is the tool. Effortful retrieval is what builds storage strength. Skills should be taught through interactive lessons. There are several tools at your disposal:

- Interactive lessons, using quizzes and light in-browser tasks
- Lessons which guide the user through a list of real-world steps to take (for instance, yoga poses)

Each of these should be based on a **feedback loop**, where the user receives feedback on their performance. This feedback loop should be as tight as possible, giving feedback immediately - and ideally automatically.

### Ground it in the learner's own system

When the topic touches tools the learner actually runs, teach against their real setup, not a generic one:

- Verify claims by running them against the learner's real tools, config and versions (read-only unless they agree), and say what you ran. A behaviour that holds in the docs may not hold in their build; an assumed setting may be silently ignored.
- Use their real errors, logs and config as examples and quiz material.
- When an experiment contradicts a source or your expectation, say so, fix the lesson, and record it in a learning record.

For quizzes, each answer should be exactly the same number of words (and characters, if possible). Vary which position holds the correct answer across questions. Don't give the user any clues about the answer through formatting or order.

## Acquiring Wisdom

Wisdom comes from true real-world interaction - testing your skills outside the learning environment.

When the user asks a question that appears to require wisdom, your default posture should be to attempt to answer - but to ultimately delegate to a **community**.

A community is a place (online or offline) where the user can test their skills in the real world. This might be a forum, a subreddit, a real-world class (budget permitting) or a local interest group.

You should attempt to find high-reputation communities the user can join. If the user expresses a preference that they don't want to join a community, respect it.

## Reference Documents

While creating lessons, you should also create reference documents. Lessons can reference these documents - they are useful for tracking raw units of knowledge useful across lessons.

Lessons will rarely be revisited later - reference documents will be. They should be the compressed essence of the lesson, in a format designed for quick reference.

Some learning topics lend themselves to reference:

- Syntax and code snippets for programming
- Algorithms and flowcharts for processes
- Yoga poses and sequences for yoga
- Exercises and routines for fitness
- Glossaries for any topic with its own nomenclature

Glossaries, in particular, are an essential reference. Once one is created, it should be adhered to in every lesson.

## `notes.md`

The user will sometimes express preferences of how they want to be taught, or things you should keep in mind. This is the place to record those preferences, so you can refer back to them when designing lessons or working with the user.

## Invocation

This skill is meant to be invoked explicitly (`/teach <topic>`), not picked up by the model on its own. The `disable-model-invocation` and `argument-hint` flags are stored under `metadata:` in the frontmatter so the file passes `agentskills validate`. A harness that only honours these as top-level keys will not see them and may auto-invoke the skill; if that matters, move them back to the top level and accept the validator warning.

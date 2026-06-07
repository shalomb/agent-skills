# Curriculum Management

This reference outlines how the Socratic Tutor manages curriculums, tracks learning progress, and adapts to the learner's preferred structure.

## The Syllabus Graph (`syllabus.md`)

When engaging in structured learning, the tutor relies on a master document for a specific curriculum, typically named `syllabus.md` or reflecting the specific topic (e.g., `AWS-Solutions-Architect-Professional-SAP-C02.md`). 

This document serves as the dependency graph of topics. The agent uses this graph to:
- Identify the learner's current position within the broader curriculum.
- Tally completed sessions.
- Determine the next logical topic, ensuring new concepts build appropriately upon prerequisite knowledge (scaffolded learning).

## Managing Learning Documents

Instead of appending all notes into a single, increasingly bloated index file, the Socratic Tutor employs a decentralized approach to documentation.

1. **Granular Session Files:** As the learner completes individual Socratic deep dives, the agent accumulates these insights into granular session files.
2. **Adjacency:** These learning documents are created and stored adjacent to the master `syllabus.md` file (in the same directory or a designated subfolder).
3. **Reference Linking:** The `syllabus.md` graph can be updated to link to these newly created session files, maintaining an organized structure of the learner's expanding knowledge base.

## Adapting to Learning Modes

The tutor seamlessly switches between two distinct modes based on the learner's needs and stated goals.

### Structured Mode
- **Graph Adherence:** The tutor rigidly tallies progress against the `syllabus.md` graph.
- **Scaffolded Learning:** Ensures that topics are introduced in the exact order defined by the curriculum, strongly enforcing prerequisite knowledge before moving forward.
- **Best For:** Preparing for certifications, academic courses, or learning complex subjects with strict linear dependencies.

### Casual Mode
- **Flexible Graph:** The dependency graph is relaxed.
- **Curiosity-Driven:** The learner's immediate curiosity drives the selection of the next topic. The tutor will still consult the syllabus for context but will not strictly enforce sequential prerequisites.
- **Documentation Maintained:** The tutor still logs and generates learning documents nearby, ensuring that even casual exploration is documented for future reference.
- **Best For:** Broad exploration, hobbyist learning, or reviewing specific topics without committing to an entire curriculum.

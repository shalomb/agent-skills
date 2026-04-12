# The Atomic Commit Protocol Specification (ACP) 1.0.0

## Summary

The Atomic Commit Protocol (ACP) is a formal specification for structuring Git micro commits. It is designed to ensure that each commit is a complete, self-contained, and logically indivisible unit of work.

By adhering to this protocol, contributors create a project history that is transparent, auditable, and highly resilient. Each commit encapsulates not only the code change but also its specification, verification, and documentation, making it independently understandable and safe to revert.

This specification is particularly suited for environments with multiple contributors, including autonomous AI agents, where clarity, context, and verifiability are paramount.

## Keywords

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html).

## Definitions

1.  **Atomic Commit**: A single Git commit that adheres to this specification. It represents a complete and coherent set of changes that can be applied to or removed from a codebase without leaving it in an inconsistent state.

2.  **Implementation**: The source code written to satisfy the requirements of a BDD Specification and pass the associated TDD Tests.

3.  **BDD Specification**: A Behavior-Driven Development specification that describes the intended behavior of a feature or change from a user or system perspective.

4.  **TDD Test**: A Test-Driven Development test written to verify a specific piece of the Implementation.

5.  **Test Graduation Ladder**: A structured approach to testing that categorizes tests into phases (e.g., Hot Zone, Full Suite) and development loops (e.g., Inner Loop, Outer Loop) to ensure comprehensive and efficient verification of changes.

## Specification

### 1. Atomic Commit Composition

An Atomic Commit is an indivisible unit composed of several distinct but related parts.

1.1. An Atomic Commit **MUST** contain one or more formal BDD specifications that describe the intended change for the end-users' benefit (aligned to a user story).

1.2. An Atomic Commit **MUST** contain a set of TDD tests that guide and validate the Implementation. At least one of these tests **MUST** fail before the Implementation is present and **MUST** pass after the Implementation is present.

1.3. An Atomic Commit **MUST** contain the minimal Implementation code required to satisfy the BDD specifications and make all included TDD tests pass.

1.4. The Implementation **MUST NOT** contain temporary files, artifacts, or debugging statements created during development.

1.5. An Atomic Commit **MUST** include updates to end-user documentation that reflect the change. This documentation **MUST** follow a structured framework (e.g., Diataxis).

1.6. The Implementation **SHOULD** include inline code comments to explain the rationale behind complex or non-obvious logic.

1.7. A single commit **MUST NOT** mix refactoring with functional changes, or reformatting with any other changes. These **MUST** be in separate commits to maintain a clear, reviewable history. For detailed guidance on the refactoring process, refer to Appendix D: Notes on Refactoring.

### 2. Commit Message Structure

The commit message is a critical component of the Atomic Commit, providing essential context and metadata. The following rules are based on and compatible with longstanding Git community conventions.

2.1. The entire commit message **MUST** conform to the [Conventional Commits specification v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

2.2. The `description` portion of the `header` (the text after the type/scope and colon) **SHOULD** be capitalized for readability, following the practice recommended by Tim Pope, though Conventional Commits examples typically use lowercase.

2.3. The `header` **MUST NOT** end with a period.

2.4. The `header` **MUST** be 50 characters or less.

2.5. The `description` portion of the `header` **MUST** be written in the imperative mood (e.g., "Add feature," not "Added feature" or "Adds feature").

2.6. A single blank line **MUST** separate the `header` from the `body`.

2.7. The `body` **MUST** explain the reasoning and context behind the change (the "why"). It **SHOULD NOT** simply repeat what the code does.

2.8. Lines in the `body` **SHOULD** be wrapped at 72 characters.

2.9. The `footer` of the commit message **MAY** include references to related issues or tickets (e.g., `Closes `).

2.10. The commit **SHOULD** be cryptographically signed (e.g., using GPG or SSH) to ensure authenticity and integrity.

### 3. Rationale and Importance for Automated Agents

While this specification is beneficial for human developers, it is foundational for autonomous or semi-autonomous software engineering agents for the following reasons:

*   **Trust and Safety**: The strict requirements for testing and specification act as a safety harness, ensuring an agent's contribution is verified and correct before it is committed.
*   **Zero-Cost Rollback**: If an agent's experiment or change introduces a regression, the Atomic Commit can be reverted cleanly and safely, returning the system to a known-good state.
*   **Observability**: The protocol forces an agent to externalize its "intent" (via BDD specs) and "reasoning" (via the commit message body), solving the "black box" problem of AI-generated code.
*   **Structured Collaboration**: The specification provides a clear, unambiguous contract for what constitutes a "done" piece of work, enabling seamless handoffs between humans and agents or between different specialized agents.

---

## Appendix A: Commentary and Exegesis

This appendix contains non-normative commentary to provide additional context for human readers.

### A.1. The Inversion of Value: Context over Code

The Atomic Commit Protocol enables a critical shift in perspective, especially in an ecosystem that includes AI-driven development. Historically, the source code has been treated as the primary asset of value. This protocol suggests an inversion: the **context** is the durable asset, and the **code** is transient.

*   **Code is Disposable**: With advanced tools and AI agents, code can be generated, refactored, or completely rewritten with increasing ease. The implementation itself becomes a commodity.
*   **Context is Durable**: The crucial, non-disposable assets are the accumulated learnings and decisions captured in the commit's context:
    *   **The BDD Specification**: *What* problem are we solving?
    *   **The TDD Tests**: *How* do we prove the problem is solved?
    *   **The Commit Message**: *Why* did we choose this solution?
    *   **The Documentation**: *How* do others use what we have built?

This collection of context is the true deliverable. It is the source of truth from which the code can be understood, validated, and reliably regenerated. Losing the code is an inconvenience; losing the context is a catastrophe.

### A.2. Rationale for Commit Message Rules

The specific rules for commit messages are not arbitrary. They are based on established community conventions that ensure the commit history is as readable and useful as possible. A well-formatted commit message is a hallmark of a professional developer (or agent).

The construction of the first line (the subject line) is especially critical. It serves as a concise summary of the changes introduced by the commit, allowing both humans and agents to quickly scan the history and decide which commits are pertinent and worth deeper consideration. If there are any technical details that cannot be expressed within its strict size constraints, they **MUST** be placed in the body instead.

The subject line is used extensively across Git tools, often in a truncated form if it exceeds length limits. Adhering to the specified format significantly enhances the utility of these tools:

*   `git log --pretty=oneline` shows a terse history mapping containing the commit ID and the summary.
*   `git rebase --interactive` provides the summary for each commit in the editor it invokes.
*   If the config option `merge.summary` is set, the summaries from all merged commits will make their way into the merge commit message.
*   `git shortlog` uses summary lines in the changelog-like output it produces.
*   `git format-patch`, `git send-email`, and related tools use it as the subject for emails.
*   Reflogs, a local history accessible with `git reflog` (intended to help recover from mistakes), get a copy of the summary.
*   `gitk` has a dedicated column for the summary.

The overall benefit of aligning this with conventional commits is a highly structured Git commit history—effectively treating Git as a navigable database—where each "breadcrumb trail" leaves clear clues for quick and easy navigation. A capitalized, imperative subject line makes the history read like a clear series of steps taken to evolve the codebase.

### A.3. The "Micro-Commit" Philosophy and Tactical Implementation

The Atomic Commit Protocol is a specific implementation of the "micro-commit" philosophy. The core mantra is to **"do one thing"** per commit. This practice is analogous to frequently "saving your game" in a video game; it provides numerous safe points to which you can make a "graceful retreat" if a chosen path proves to be a mistake.

This philosophy can be put into practice with specific, tactical workflows:

*   **TDD Workflow Mapping**: The "Red-Green-Refactor" cycle of Test-Driven Development can be mapped directly to commits. A developer might make a commit after writing a failing test (Red), another after making it pass (Green), and a third after a subsequent refactoring.
*   **Tactical Tooling**: Achieving a clean history of atomic commits does not mean every local save must be a perfect commit. Tools should be used tactically. `git stash` is excellent for context switching, and `git rebase --interactive` is a powerful tool for cleaning up, reordering, and squashing local, experimental commits into a clean series of atomic commits before sharing them with the team.

### A.4. Alignment with Development Best Practices

The Atomic Commit Protocol aligns with and reinforces several modern development methodologies:
-   Behavior-Driven Development (BDD) and Test-Driven Development (TDD)
-   Architectural Decision Records (ADRs)
-   Working in Small, high-quality increments
-   Continuous Integration and Frequent Merging

### A.5. Key Outcomes

Adherence to this protocol leads to tangible benefits for quality and velocity:
-   A streamlined workflow with faster delivery of robust features.
-   A high-context, information-dense codebase and version history.
-   Continuous and consistent documentation that evolves with the code.
-   Reduced "bus factor" and enhanced business continuity.
-   Comprehensive test coverage that enables teams to "fail fast."
-   Improved code quality, maintainability, and operational excellence.

## Appendix B: Example Atomic Commit Message

The following provides a concrete example of a commit message that adheres to the Atomic Commit Protocol.

```
fix(auth): add JWT token validation to login

The authentication system was rejecting valid login attempts due to
missing token validation logic. This was causing user frustration and
support escalations. Investigation revealed that while token generation
was implemented, the validation step was never added during the initial
authentication feature work.

We chose JWT tokens over session-based auth because our architecture is
moving toward stateless microservices, and JWT allows for distributed
validation without shared session state. The argon2 hashing algorithm
was selected for password storage as it provides better resistance to
GPU-based attacks than bcrypt.

This change completes the authentication flow by implementing the
missing validation logic. The fix ensures login attempts are properly
verified against generated tokens, closing the gap in the auth system.

Impact:
- Login flow now correctly validates authentication tokens
- Registration and login endpoints will both use this validation
- No breaking changes to existing API contracts
- Password storage upgraded to argon2 (more secure than previous)

Testing:
- Inner Loop (RED/GREEN): Created failing test for argon2-hash.js,
  implemented validation logic, all tests pass
- Full test suite: Phase 1 (Critical) - passed changed file tests,
  Phase 2 (Fast) - 450 tests/0 failures, Phase 3 (Validation) - 12
  slow tests + 4 E2E/0 failures

Closes 
Relates #456

Signed-off-by: Your Name <your.name@example.org>
```

## Appendix C: Example Workflow Pattern

The following is a concrete example of how the Atomic Commit Protocol can be implemented as a workflow pattern for a single fix or feature.

Each cycle follows the **RED → GREEN → REFACTOR** workflow:

1.  **Identify Gap**: The process begins with discovering a bug, identifying a needed feature, or recognizing a gap in module usage.

2.  **BDD/TDD Test Planning (RED)**:
    *   Write a BDD specification for the change if it's a new or modified feature.
    *   Write a specific, failing unit test that reproduces the bug or defines the new functionality. This is the **RED** state.

3.  **BDD Step Definitions**:
    *   If BDD is used, write the necessary step definition code to make the BDD scenarios executable.

4.  **Implementation (GREEN)**:
    *   Write the minimum amount of implementation code required to make the failing test(s) pass. This is the **GREEN** state.

5.  **Testing & Validation**:
    *   **Inner Loop 1**: Run local tests to ensure all tests pass (e.g., `make test`).
    *   **Inner Loop 2**: If generated code is affected, validate it for a fail-early plan against the system (e.g., `terraform init && terraform validate && terraform plan`).
    *   **Outer Loop 1**: Run a broader workflow to verify no regressions in functionality have been introduced in the wider system (e.g., `terraform apply && make smoke-test && make uat`). In reality, this is likely to be something a CI/CD pipeline handles.
    *   **Outer Loop 2**: Run an even broader workflow to verify no regressions have been introduced in the NFRs of the wider system (e.g., `make test-performance`). In reality, this is likely to be something a CI/CD pipeline working with other test/validation harnesses handles.

6.  **Refactor** (as needed):
    *   With the safety of passing tests, improve the code's structure, readability, or performance.
    *   Clean up temporary comments and remove any debugging prints.
    *   Delete any unused code, temporary files, or artifacts created during development.

7.  **Documentation**:
    *   Update inline code comments, README files, or other relevant documentation to reflect the changes.

8.  **Atomic Commit**:
    *   Commit the change atomically with a clear message that follows the rules in this specification.
    *   The commit message body **SHOULD** include evidence of testing and a description of the expected impact.

## Appendix D: Notes on Refactoring

Refactor (as needed):

1. With the safety of passing tests, improve the code's structure, readability, or performance.
2. **TCR Micro-Refactoring Practice:** When performing structural changes, developers **SHOULD** adopt the Test -> Commit -> Revert (TCR) principle: work in extremely small, isolated steps, running local tests frequently. If a structural improvement breaks a test, **immediately revert** that small change to maintain the GREEN state, then attempt a safer, smaller refactoring step.
3. Clean up temporary comments and remove any debugging prints.
4. Delete any unused code, temporary files, or artifacts created during development.

## Appendix E: Adoption Guidelines

| **Agent Action**             | **Based on Step**          | **Convention Goal**                                                                                                                                                                                           |
| ---------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Commit Only Passing Code** | **Implementation (GREEN)** | Never commit code with failing tests. The **GREEN** state is the prerequisite for the next step.                                                                                                              |
| **Apply the Cleanup List**   | **Refactor**               | **Must** check off cleaning up debugging prints, temporary comments, and unused code. This is non-negotiable code hygiene.                                                                                    |
| **Improve Code Design**      | **Refactor**               | **Should** identify opportunities for improving code clarity, removing duplication, or simplifying complex logic. If a test passes, but the code is messy, a refactoring cycle is warranted before moving on. |
| **Document Changes**         | **Documentation**          | Reflect the new, cleaner structure in the documentation.                                                                                                                                                      |

## Appendix F: Test Graduation Ladder

|**Development Loop**|**Test Phase Recommended**|**Test Target**|
|---|---|---|
|**Inner Loop (RED → GREEN Iteration)**|Phase 1 (Hot Zone)|`just test-critical` or `just test-changed`|
|**Refactor Safety Check**|Phase 1 (Hot Zone)|`just test-critical` or `just test-changed`|
|**Outer Loop (Pre-Commit/Pre-PR)**|Phase 1 → 2 → 3 (Full Suite)|`just test`|

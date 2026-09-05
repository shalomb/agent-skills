# Example Architecture Decision Record

This worked example illustrates the complete standard in practice: Intention-Revealing title, Advice Process stakeholders, Domain Framework alignment, Tabular Y-Statement, Architectural Reification, Multi-Criteria Matrix, balanced consequences, and concrete revisit criteria.

---

# ADR-0014: Ephemeral Request De-duplication for Webhook Processing

- **Status:** Accepted
- **Date:** 2026-04-12
- **Decider(s):** Jane Doe (Principal Architect), Alex Smith (Tech Lead)
- **Consulted:** SRE Team (Maria K.), Payments Team (David L.), Security (Priya N.)
- **Informed:** Core Engineering, Partner Integrations
- **Supersedes:** N/A

## Context

Our external payment provider delivers webhook notifications for transaction state changes (e.g., `payment.settled`, `refund.failed`). Under network jitter or provider retry surges, the provider delivers duplicated webhook payloads within milliseconds or seconds of each other.

Currently, handlers process webhooks by querying the transactional PostgreSQL database to inspect prior state. Under peak surge (500+ webhooks/sec), concurrent duplicate requests cause database row-lock contention, read-modify-write race conditions, and transient connection pool exhaustion.

The core tension is balancing **strict idempotency guarantees** with **low-latency webhook acknowledgement** without overwhelming our primary relational database.

## Domain Quality Framework Alignment

- **Domain Archetype:** Distributed Systems & Data Architecture / Application Code
- **Primary Frameworks:** Distributed Data & Idempotency Principles + ISO/IEC 25010 (Software Quality) + AWS WAF
- **Guiding Quality Pillars:**
  1. *Idempotency & Deduplication (Distributed Data):* Guarantee exact-once business processing under at-least-once transport retries.
  2. *Performance Efficiency (AWS WAF) & Latency:* Acknowledge webhooks within sub-15ms without saturating transactional database connection pools.
  3. *Testability & Modifiability (ISO 25010):* Keep handlers decoupled from external cache implementation details via an in-memory test harness.

## Decision

We will implement an **ephemeral request de-duplication layer** at the API gateway entry point using distributed atomic locks with a short TTL (10 minutes). Incoming webhook payloads are keyed by provider event ID and hashed request fingerprint. If an identical event is already processing or was recently processed, the gateway short-circuits with an HTTP `200 OK` (acknowledging receipt) without dispatching downstream database transactions.

## Y-Statement

| Dimension | Detail |
|---|---|
| **Context** | External webhook ingestion under provider retry surges (500+ req/s) |
| **Constraint(s)** | PostgreSQL connection pool saturation; sub-50ms acknowledgement SLA |
| **Requirement(s)** | Strict transactional idempotency and database connection stability |
| **Decision** | Ephemeral distributed edge locking layer with 10-minute TTL |
| **Alternatives Rejected** | Database-level unique constraints; local in-memory LRU cache |
| **Rationale** | Short-circuits duplicate delivery at the perimeter before database connection dispatch |
| **Tradeoff Accepted** | Operational dependency on Redis cluster; distributed lock-lease failure modes |
| **Decision Authority** | Principal Architect (Jane Doe) — Approved 2026-04-12 |

## Architectural Reification & Enforcement

This decision is enforced mechanically through the following system constructs:

1. **Explicit Domain Type:** An immutable `IdempotencyKey` value object validates and sanitizes all incoming event IDs before handlers can accept them.
2. **Middleware Boundary:** An `IdempotencyMiddleware` intercepts requests ahead of the route dispatcher. Handlers have no direct access to raw un-deduplicated requests.
3. **CI Architecture Fitness Function:** An ArchUnit / import-linter rule asserts that webhook handler packages cannot import raw database session pools directly; they must inherit through the idempotent dispatch pipeline.
4. **Telemetry & Alarms:** Metrics track `webhook.dedup.hit_count` and `webhook.dedup.lock_timeout_count`. An alarm triggers if cache fallback errors exceed 0.5% in a 5-minute window.

## Consequences

### Positive Outcomes (+ Gains)
+ Eliminates concurrent duplicate execution and database row-lock contention.
+ Database connection pool usage during provider retry storms remains constant.
+ Average webhook response latency drops from 45ms to 8ms for duplicate deliveries.

### Negative Consequences & Trade-offs (- Costs & Accepted Debt)
- Introduces operational dependency on Redis cluster availability for incoming webhooks.
- If Redis becomes unavailable, the system fails open to database-level row locking with degraded latency (fallback complexity).
- Risk of lock abandonment if a worker node crashes mid-execution; mitigated with an aggressive 30-second lease timeout.

## Alternatives Considered

### Multi-Criteria Comparison Matrix

| Evaluation Criterion | Option A (Edge Redis Lock - Chosen) | Option B (DB Unique Constraint) | Option C (In-Memory LRU) |
|---|---|---|---|
| **Cost / TCO** | Low (shares existing cluster) | Zero additional infra spend | Zero additional infra spend |
| **Operational Overhead** | Medium (monitors Redis latency) | Low (uses existing DB) | Low (no external service) |
| **Latency Under Surge** | Sub-10ms (cache hit) | 45–120ms (lock contention) | Sub-1ms (local heap) |
| **Idempotency Accuracy** | 100% across all 12 nodes | 100% (atomic DB abort) | Fails (~40% misses across nodes) |
| **Reversibility** | High (isolated in gateway middleware) | Medium (schema constraint) | High (isolated in middleware) |
| **Domain Framework Fit** | High (WAF Perf + Distributed Idempotency) | Poor (fails WAF Perf under surge) | Poor (violates consistency) |

### Option A: Edge Distributed Lock (Chosen)
- **Why Chosen:** Guarantees cluster-wide deduplication with sub-10ms response times before hitting relational connection pools.
- **Key Caveat:** Requires monitored cache cluster fallback.

### Option B: Database Unique Constraint & Optimistic Locking
- **Description:** Rely strictly on PostgreSQL unique constraints on `(provider_event_id)` and catch transaction rollback errors.
- **Strongest Argument:** Uses existing persistent storage without introducing new infrastructure.
- **Why Rejected:** Concurrent inserts still incur write-lock contention, connection exhaustion under retry bursts, and high database CPU spikes during surges.

### Option C: Local In-Memory LRU Cache per API Instance
- **Description:** Maintain an in-memory bloom filter / LRU cache within each container process.
- **Strongest Argument:** Zero network latency and zero external operational dependencies.
- **Why Rejected:** Webhooks are load-balanced across 12 horizontal container instances; duplicates hit different instances, rendering local in-memory caches ineffective.

## Revisit Criteria

- If aggregate webhook volume exceeds 20,000 req/s, evaluate transitioning from synchronous edge locking to an asynchronous streaming buffer (e.g., Kafka / SQS outbox).
- If the payment provider introduces guaranteed single-delivery HTTP transports or mutual TLS message signing with server timestamps that simplify verification.

# Example Architecture Decision Record

This worked example illustrates the Core Architectural Qualities in practice: Intention-Revealing title, Advice Process stakeholders, Y-Statement, Architectural Reification, balanced consequences, and realistic alternatives.

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

## Decision

We will implement an **ephemeral request de-duplication layer** at the API gateway entry point using distributed atomic locks with a short TTL (10 minutes). Incoming webhook payloads are keyed by provider event ID and hashed request fingerprint. If an identical event is already processing or was recently processed, the gateway short-circuits with an HTTP `200 OK` (acknowledging receipt) without dispatching downstream database transactions.

## Rationale (Y-Statement)

In context of external webhook ingestion under provider retry surges,  
facing concurrent duplicate deliveries causing database lock contention and race conditions,  
we decided for an ephemeral distributed locking and caching layer at the edge  
to achieve strict idempotency and stable database connection overhead,  
accepting distributed cache dependency and potential lock leak failure modes.

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

### Option A: Database Unique Constraint & Optimistic Locking
- **Description:** Rely strictly on PostgreSQL unique constraints on `(provider_event_id)` and catch transaction rollback errors.
- **Strongest Argument:** Uses existing persistent storage without introducing a distributed caching tier or new infrastructure.
- **Why Rejected:** Concurrent inserts still incur write-lock contention, connection exhaustion under retry bursts, and high database CPU spikes during surges.

### Option B: Local In-Memory LRU Cache per API Instance
- **Description:** Maintain an in-memory bloom filter / LRU cache within each Node.js process.
- **Strongest Argument:** Zero network latency and zero external operational dependencies.
- **Why Rejected:** Webhooks are load-balanced across 12 horizontal container instances; duplicates frequently hit different instances, rendering local in-memory caches ineffective.

## Revisit Criteria

- If aggregate webhook volume exceeds 20,000 req/s, evaluate transitioning from synchronous edge locking to an asynchronous streaming buffer (e.g., Kafka / SQS outbox).
- If the payment provider introduces guaranteed single-delivery HTTP transports or mutual TLS message signing with server timestamps that simplify verification.

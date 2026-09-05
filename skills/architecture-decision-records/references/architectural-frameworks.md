# Architectural Evaluation Frameworks by Domain

When authoring or reviewing an ADR, evaluate the decision against the established industry framework matching the domain archetype. Architectural decisions cannot be evaluated in a vacuum—different domains prioritize different qualities.

---

## 1. Cloud & Infrastructure Architecture

Use for cloud topologies, Terraform/IaC modules, serverless/container platforms, networking, and cloud services.

### Primary Framework: AWS & Azure Well-Architected Framework (WAF)

| Pillar | Core Architectural Question | Key Verification Criteria |
|---|---|---|
| **Operational Excellence** | How do we run, monitor, and evolve the workload? | Infrastructure as code, automated deployments, health telemetry, runbooks, rollback safety. |
| **Security** | How do we protect data, identities, and systems? | Principle of least privilege, zero-trust network boundaries, encryption in transit/at rest, secrets management, blast radius containment. |
| **Reliability** | How does the workload recover from infrastructure or service disruptions? | Multi-AZ/region redundancy, graceful degradation, circuit breakers, recovery time/point objectives (RTO/RPO), self-healing. |
| **Performance Efficiency** | How do we use compute and storage resources efficiently? | Right-sizing, caching strategies, asynchronous processing, serverless scaling, latency profiles under peak load. |
| **Cost Optimization** | How do we eliminate unneeded expenses and avoid cost cliffs? | Pay-per-use vs. provisioned spend, egress traffic modeling, cold storage tiering, break-even thresholds. |
| **Sustainability** | How do we minimize environmental footprint? | Resource utilization efficiency, right-scaling compute cycles, decommissioning idle resources. |

---

## 2. Software & Code Architecture

Use for application design, module boundaries, domain models, library abstractions, refactoring, and code organization.

### Primary Frameworks: ISO/IEC 25010 Quality Model + Evolutionary Architecture + DDD

| Quality Dimension | Core Architectural Question | Key Verification Criteria |
|---|---|---|
| **Maintainability & Modifiability** | Can future engineers safely change this code? | Single Responsibility, low coupling, high cohesion, clear dependency direction (Hexagonal / Clean Architecture). |
| **Testability** | Can business logic be tested deterministically in isolation? | Fast unit-level execution, in-memory isolation, mockability of external IO, deterministic time and state. |
| **Cognitive Load & Intention** | Does the design communicate its purpose clearly? | Intention-revealing interfaces, ubiquitous domain language, minimal mental indirection, avoiding accidental complexity. |
| **Architectural Reification** | Are invariants enforced mechanically by the system? | Explicit domain value types, compiler-enforced state machines, package visibility barriers, automated CI fitness functions. |
| **Architectural Fitness Functions** | How do we prevent architectural erosion over time? | ArchUnit tests, import-linter rules, structural code checks in CI asserting that dependency rules are never violated. |
| **Evolvability & Extensibility** | Can new capabilities be added without rewriting existing code? | Open-Closed Principle, strategy patterns, pluggable seams, preserving two-way doors. |

---

## 3. Distributed Systems & Data Architecture

Use for messaging queues, event streaming, data pipelines, database selection, caching tiers, and microservice communication.

### Primary Frameworks: CAP / PACELC Theorem + Data Mesh & Streaming Principles

| Quality Dimension | Core Architectural Question | Key Verification Criteria |
|---|---|---|
| **Consistency vs. Availability / Latency** | Under network partition, do we prioritize consistency or availability? | ACID vs. eventual consistency, read-your-own-writes guarantees, saga orchestration vs. choreography. |
| **Idempotency & Deduplication** | How do we handle network retries and duplicate events? | Distributed idempotency keys, atomic lease locking, deduplication windows, at-least-once vs. exactly-once semantics. |
| **Schema Evolvability & Governance** | How do schemas evolve without breaking consumers? | Backward and forward compatibility (Protobuf / Avro / JSON Schema), explicit deprecation contracts. |
| **Data Lineage & Auditability** | Can state transitions be reconstructed and audited? | Immutable event logs, audit trails, event sourcing, tracing headers propagated across asynchronous boundaries. |
| **Backpressure & Load Decoupling** | How does the system handle sudden traffic spikes? | Buffer queues, rate limiters, backpressure signaling, dead letter queues (DLQs) for poisoning messages. |

---

## How to Apply in an ADR

1. **Select the Domain Archetype:** Determine if the decision is primarily Cloud/Infra, Software/Code, or Data/Distributed (or a combination).
2. **Select 2–3 Driving Pillars/Qualities:** Identify which specific qualities forced the decision (e.g., *Software: Testability & Modifiability* vs. *Cloud: Cost Optimization & Reliability*).
3. **Document in the Template:** Fill out the `## Domain Quality Framework Alignment` section with the selected pillars and explicit rationale.

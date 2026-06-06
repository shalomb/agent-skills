# Commensurate Scaling

## Context/Problem
As demand (traffic, data, or computing) increases by an order of magnitude N, system architectures often experience exponential growth in resource costs, operational overhead, and development effort. Traditional vertical scaling (buying bigger machines) or tightly coupled stateful architectures hit physical and financial ceilings quickly, leading to cascading failures under heavy load.

## Solution/Pattern
Design systems so that the cost and effort to handle growth does not exceed N. This is achieved through the Core Principles for Commensurate Scaling:
- **Horizontal over Vertical Scaling**: Distribute load across a larger pool of commodity instances rather than upgrading to expensive vertical machines.
- **Statelessness**: Decouple compute from state to allow rapid, automated scaling without synchronizing local user sessions.
- **Data Partitioning (Sharding)**: Distribute large datasets across multiple database nodes based on a partition key for linear scaling of read/write operations.
- **Loose Coupling**: Utilize microservices and asynchronous event-driven communication (e.g., Kafka) to prevent traffic spikes in one module from cascading.
- **Smart Caching**: Use in-memory caches (e.g., Redis) or CDNs to mitigate redundant computations and database queries.
- **Distributed Limits and Queuing**: Use backpressure and rate-limiting to hold requests in queues rather than failing immediately under massive load.

## Example
Instead of deploying a monolithic web server with local session storage attached to a single massive relational database, use stateless microservices running in an Auto Scaling Group behind a load balancer. Offload session state to a Redis cache, communicate via a Kafka message queue, and shard the underlying database. As traffic doubles, you can simply spin up twice as many cheap instances without changing the architecture.

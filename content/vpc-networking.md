# VPC networking and cold starts

Attaching a serverless function to a private network can add to cold-start time
because the platform may need to set up network interfaces and routing before the
environment can reach other resources. Historically this network setup was one of
the largest contributors to cold-start latency for functions inside a virtual
private cloud.

Modern platforms have reduced this cost by preparing shared network interfaces
ahead of time, so the per-environment networking overhead on a cold start is much
smaller than it once was. Even so, functions that open connections to databases
or caches during initialization still pay that connection-setup time on every
cold start.

To keep networking cheap on cold starts, place functions and the resources they
talk to in the same region and availability zone, reuse connections across
invocations instead of reconnecting on every request, and lazily initialize
clients so that a request that does not need the database is not slowed by
connecting to it.

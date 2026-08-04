# Reducing cold starts with provisioned concurrency

Provisioned concurrency keeps a configured number of execution environments
initialized and ready to respond immediately. Instead of waiting for the
platform to create an environment on demand, requests are routed to environments
that have already downloaded your package, started the runtime, and run your
initialization code. This removes the cold-start penalty for as many concurrent
requests as you provision.

Provisioned concurrency is the most direct way to eliminate cold starts for
latency-sensitive endpoints, such as user-facing APIs where a multi-second first
request is unacceptable. You pay for the reserved capacity whether or not it is
used, so it is a trade-off between predictable latency and cost.

A common pattern is to schedule provisioned concurrency around known traffic:
provision more capacity during business hours or ahead of a launch, and scale it
back down overnight. Autoscaling policies can also adjust provisioned
concurrency based on utilization, so you keep warm capacity in proportion to
real demand rather than paying for a fixed peak all day.

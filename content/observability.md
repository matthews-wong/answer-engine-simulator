# Measuring and monitoring cold starts

You cannot tune what you cannot see, so the first step in managing cold starts is
measuring them. Most platforms emit an initialization-duration metric or log
field that marks which invocations paid a cold start and how long the
initialization took, separate from the time spent running your handler.

Track cold starts as a percentage of total invocations and watch the latency
distribution rather than the average. Because warm environments serve most
requests, cold starts hide in the tail: the p50 latency can look healthy while
p99 latency is dominated by cold starts. Alerting on high-percentile latency is
usually more actionable than alerting on the mean.

Correlate cold-start spikes with deploys and traffic patterns. A burst of cold
starts right after a deployment is expected, while a steady stream during normal
traffic suggests environments are being reclaimed and re-created. This signal
tells you whether the right fix is provisioned concurrency, a smaller package, or
simply keeping environments warm.

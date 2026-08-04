# What causes serverless cold starts

A cold start happens when a serverless platform has to create a brand-new
execution environment before it can run your function. The platform downloads
your deployment package, starts the language runtime, and only then runs your
initialization code. All of that latency is added to the very first request the
new environment serves.

Cold starts occur when there is no warm environment available: the first
invocation after a deploy, a sudden spike in traffic that needs more
environments than are currently running, or an environment being reclaimed after
a period of inactivity. Once an environment is warm it can serve many subsequent
requests with no cold-start penalty, so cold starts are a tail-latency problem
rather than an average-latency one.

The size of the penalty depends on the runtime, the size of your deployment
package, and how much work your initialization code does. A tiny function on a
fast-starting runtime may add tens of milliseconds, while a large package on a
heavy runtime that also connects to a database on startup can add several
seconds to that first request.

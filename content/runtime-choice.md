# Choosing a runtime for faster cold starts

Different language runtimes have very different cold-start characteristics
because they differ in how much work happens before your code runs. Lightweight
interpreted runtimes and small compiled binaries tend to initialize in tens of
milliseconds, while runtimes that start a virtual machine and load large
framework classes can take noticeably longer.

Runtimes built around a heavy virtual machine typically show the largest
cold-start penalty, since the VM must start and just-in-time compilation has not
yet warmed up. Interpreted runtimes such as scripting languages, and ahead-of-time
compiled languages that ship a single native binary, generally start fastest.

Runtime choice interacts with the rest of your cold-start budget. A fast runtime
paired with a bloated package or heavy initialization can still be slow, while a
heavier runtime with disciplined startup code and provisioned concurrency can hit
strict latency targets. Treat runtime as one lever among several rather than a
decision made in isolation.

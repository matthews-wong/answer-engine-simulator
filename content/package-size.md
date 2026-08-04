# How deployment package size affects cold starts

The larger your deployment package, the longer the platform takes to download
and unpack it into a new execution environment, and that time is paid on every
cold start. Trimming package size is one of the cheapest ways to shrink
cold-start latency because it requires no extra reserved capacity.

Common ways to reduce package size include removing unused dependencies,
excluding development and test files from the build, and avoiding bundling large
assets that could be fetched at runtime instead. Tree-shaking and minification
help for interpreted runtimes, while for compiled runtimes a smaller static
binary starts faster.

Shared libraries or layers can also help: moving heavy, rarely-changing
dependencies into a separate layer keeps your function package small and lets the
platform cache the layer across deployments. The goal is to make the code the
platform must fetch on a cold start as small as possible without hiding startup
cost elsewhere.

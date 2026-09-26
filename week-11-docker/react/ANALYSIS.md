# Multi-stage result — Eze Favour

1. The single-stage image is 854,614,809 bytes; the multi-stage image is 94,232,874 bytes, measured using Docker image inspection on the same host.
2. `(854614809 - 94232874) / 854614809 × 100` gives an **88.97% reduction** (89.0% rounded).
3. The runtime contains the compiled React assets and Nginx rather than the Node build toolchain and development dependencies.
4. Fewer shipped components reduce the attack surface; smaller size alone does not prove that every package is secure.
5. The smaller image reduces bytes to distribute, although this exercise did not benchmark pull time or bandwidth.
6. Copying package manifests before application source lets Docker reuse the dependency-install layer when only source changes.
7. The final runtime uses UID 101, a healthcheck, a read-only filesystem and temporary writable paths; it serves the build on host port 80.
8. Builds, measurements and browser checks were performed by Codex under my delegation; raw records and source are linked in Assignment 2.

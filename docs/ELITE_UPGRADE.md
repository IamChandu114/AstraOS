# AstraOS Elite Upgrade

This upgrade moves AstraOS toward an autonomous AI-native infrastructure runtime while keeping telemetry honest: unavailable host capabilities are reported as unavailable instead of simulated.

## Implemented Runtime Capabilities

- Real host telemetry: CPU, per-core load, memory, swap, process state, disk I/O, network I/O, GPU through `nvidia-smi` when present, thermal sensors when exposed by the host, battery, and kernel procfs when available.
- Optimization execution layer: guarded `renice`, CPU affinity, process isolation, Linux cgroup throttle planning, and memory pressure recommendations. Apply mode requires `ASTRAOS_ENABLE_APPLY=1`.
- Protected process safety: shared filtering prevents OS-critical processes such as Windows system services and Linux kernel threads from being selected as optimization or healing targets.
- Self-healing infrastructure: detects runaway CPU, memory leak candidates, system memory pressure, and AI resource anomalies, then generates mitigation timelines.
- Workload classification: recognizes browser-heavy, AI inference, rendering, compiler-heavy, gaming, background compute, containerized, and distributed workload patterns.
- Security analysis: scores suspicious process/network behavior using process telemetry and avoids broad substring false positives.
- Container and cloud awareness: inspects Docker and Kubernetes through real local CLIs with a short cache to keep the dashboard responsive.
- Kernel observability: detects `bpftrace` and `perf` on Linux and exposes capability/status endpoints; Windows hosts correctly report unsupported.
- Digital twin: projects near-future CPU, memory, thermal risk, and strategy from telemetry history.
- Scheduler simulator: compares Linux CFS-style assignment with AstraOS load-balanced placement using current process telemetry.
- Adaptive training pipeline: generates versioned model artifacts from stored telemetry.
- Research report mode: `/research-report` emits architecture, prediction, benchmark, scheduler, and healing analysis from live runtime state.

## How To View

Dashboard:

```text
http://127.0.0.1:5173
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Elite runtime JSON:

```text
http://127.0.0.1:8000/elite/status
```

Smoke test:

```powershell
python scripts\demo_pipeline.py
```

## Host Capability Notes

- On Windows, eBPF, perf, procfs kernel counters, and most thermal sysfs sensors are unavailable. AstraOS reports these limitations explicitly.
- Docker and Kubernetes are only shown as active when the local Docker/Kubernetes CLIs return real workloads.
- Real host-changing optimization is intentionally blocked unless `ASTRAOS_ENABLE_APPLY=1` is set.

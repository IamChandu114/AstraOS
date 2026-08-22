# AstraOS Production Infrastructure Upgrade

This upgrade turns the runtime into a stronger infrastructure intelligence platform while keeping real telemetry honest.

## Added

- Distributed local fabric with four modeled nodes:
  - `astra-node-1`: CPU-heavy edge worker
  - `astra-node-2`: memory-pressure worker
  - `astra-node-3`: network-heavy gateway
  - `astra-node-4`: idle failover worker
- Live node health, uptime, CPU, memory, network, role, workload, and task counts.
- Orchestration recommendations when a node crosses pressure thresholds.
- Live operational event stream via `/events` and `/ws/events`.
- Distributed telemetry stream via `/distributed/status` and `/ws/distributed`.
- Stress controls via `POST /stress/{cpu|memory|network|thermal}`.
- Proof mode data endpoint at `/proof/live`.
- Dashboard proof route at `http://127.0.0.1:5173/proof/live`.
- Architecture endpoint at `/architecture`.
- Dashboard architecture route at `http://127.0.0.1:5173/architecture`.
- Capability matrix replacing vague unavailable states with explicit adapter explanations.

## Real vs Simulated

- Host telemetry remains real: CPU, memory, processes, disk, network, battery, GPU adapter, thermal adapter, and kernel adapter state come from actual collectors.
- Distributed nodes are deterministic local infrastructure simulation for recruiter/demo orchestration. They are labeled through the API as `deterministic_local_node_simulation`.
- Linux-only tooling such as eBPF, perf, sysfs thermal zones, and cgroups reports inactive on unsupported hosts instead of pretending to exist.

## Run

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
cd dashboard
npm run dev -- --host 127.0.0.1 --port 5173
```

## View

```text
Dashboard:     http://127.0.0.1:5173
Proof Mode:    http://127.0.0.1:5173/proof/live
Architecture:  http://127.0.0.1:5173/architecture
API Docs:      http://127.0.0.1:8000/docs
```






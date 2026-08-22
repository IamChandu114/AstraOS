# AstraOS Recruiter Demo

This is the shortest path to present AstraOS as a real AI-native infrastructure runtime.

## 1. Start Runtime

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd dashboard
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
http://127.0.0.1:8000/docsz
http://127.0.0.1:8000/proof/live
```

## 2. Prove It Is Real

Run:

```powershell
python scripts/final_health_check.py
```

Show:

- `/metrics` streams live host telemetry.
- `/proof/live` exposes raw collector payloads, process IDs, predictions, capabilities, and benchmark evidence.
- `/root-cause` explains why runtime pressure is happening.
- `/predictive/alerts` shows future failure alerts with ETA, confidence, why, recommendations, and impact simulation.
- `/executive-summary` summarizes reliability, active predictive alerts, and downtime prevented.
- `/incidents` shows detection, prediction, execution, and recovery timeline.

## 3. Dashboard Story

Narrate this flow:

1. AstraOS collects CPU, memory, disk, network, process, GPU, battery, and thermal adapters when the host exposes them.
2. The AI runtime classifies workload behavior and predicts pressure.
3. Root-cause analysis identifies correlated processes and explains the decision.
4. The optimization engine generates a protected plan.
5. Apply mode is gated by `ASTRAOS_ENABLE_APPLY=1` for safety.
6. Before/after proof records the measurable impact.
7. The distributed fabric shows four node roles and chaos orchestration.
8. Recruiter Demo Mode shows the loop: Observe -> Predict -> Decide -> Act -> Verify.
9. The Reliability Index and Downtime Prevention Counter translate AI operations into business value.

## 4. Chaos Demo

```powershell
Invoke-WebRequest -Method POST "http://127.0.0.1:8000/chaos/cpu?duration_seconds=90"
Invoke-WebRequest -Method POST "http://127.0.0.1:8000/chaos/node_crash?duration_seconds=90"
```

Then show:

- Live Infrastructure Logs
- Incident Timeline
- Distributed Edge
- Multi-Node Infrastructure
- Predictive Notification Center
- Prediction Timeline

## 5. Optimization Proof Demo

Planning mode:

```powershell
Invoke-WebRequest "http://127.0.0.1:8000/optimize"
```

Protected apply mode:

```powershell
$env:ASTRAOS_ENABLE_APPLY="1"
Invoke-WebRequest -Method POST "http://127.0.0.1:8000/optimize?apply=true"
Invoke-WebRequest "http://127.0.0.1:8000/optimization/proof"
```

Safety notes:

- Critical OS processes are protected.
- Apply mode is disabled by default.
- Rollback metadata is captured when supported.

## 6. Best Recruiter Talking Points

- Real telemetry first, simulation only when clearly labeled.
- AI explains decisions instead of just showing charts.
- Low-level Linux hooks are represented through `renice`, CPU affinity, cgroups, `/proc`, sysfs, perf, and eBPF adapters.
- Distributed node runtime can use Docker Compose node agents.
- Proof mode destroys the “fake dashboard” concern by exposing raw runtime payloads.

# Demo Scenario

## Setup

Run the monitoring daemon, AI predictor, scheduler planner, distributed orchestrator, and dashboard.

## Storyboard

1. Heavy workload starts.
2. CPU utilization rises above 80%.
3. Thermal sensor crosses 88 C.
4. AI predicts overload within 18 seconds.
5. Scheduler moves inference to a performance core.
6. Background tasks move to efficiency cores.
7. Edge orchestrator distributes inference across laptop, Jetson Nano, and Raspberry Pi.
8. Dashboard shows lower thermal peak, reduced latency, and higher inference FPS.

## Expected Decision Log

```text
Predicted CPU overload in 18 seconds.
Predicted temperature: 94 C.
Optimization mode activated.
Move AI inference to Performance Core 2.
Move background tasks to Efficiency Core 4.
AI workload distributed: Laptop 42%, Jetson Nano 36%, Raspberry Pi 22%.
Thermal peak reduced to 81 C.
```

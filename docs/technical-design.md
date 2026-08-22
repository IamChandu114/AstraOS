# AstraOS Technical Design

## Control Plane

The control plane receives one-second metrics from the monitoring daemon, runs prediction, ranks optimization policies, and emits actions. Actions stay explicit and inspectable so privileged operations can be audited.

## Data Plane

The data plane covers CPU affinity, process priority, memory-pressure handling, thermal migration, power policies, and edge workload placement.

## Safety Model

- Default mode is dry-run.
- Privileged Linux changes require `--apply`.
- Optimization plans are serializable JSON.
- Real kernel module work is kept as future expansion.

## AI Runtime

The runtime combines:

- LSTM architecture for temporal workload traces.
- Random Forest for short-horizon CPU and temperature forecasts.
- Isolation Forest style memory anomaly scoring.
- Reinforcement-style reward ranking for action selection.

## Monitoring Cadence

The C++ daemon emits telemetry once per second. That matches the target project requirement while avoiding unnecessary kernel polling overhead for a research prototype.

# Monitoring Engine

Linux C++ telemetry daemon for AstraOS.

## Capabilities

- CPU utilization from `/proc/stat`.
- RAM pressure from `/proc/meminfo`.
- Process state, thread count, and top CPU consumer from `/proc/<pid>/stat`.
- Thermal sensor scan from `/sys/class/thermal`.
- Battery state from `/sys/class/power_supply`.
- Network throughput from `/proc/net/dev`.

## Build

```bash
g++ -std=c++17 -O2 -pthread system_monitor.cpp -o astra-monitor
```

## Run

```bash
./astra-monitor --interval 1
./astra-monitor --interval 1 --json
```

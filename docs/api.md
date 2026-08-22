# AstraOS JSON Interfaces

## Monitoring Snapshot

```json
{
  "cpu_usage": 76.0,
  "ram_used_gb": 5.8,
  "ram_total_gb": 8.0,
  "temperature_c": 82.0,
  "battery": "Discharging 64%",
  "network_kbps": 1430.0,
  "top_process": {"pid": 4281, "name": "chrome", "state": "S", "threads": 33}
}
```

## AI Prediction

```json
{
  "cpu_spike_probability": 0.86,
  "predicted_cpu_18s": 93.5,
  "predicted_temperature_c": 94.0,
  "memory_anomaly_score": 0.34,
  "action": "THERMAL_MIGRATION",
  "confidence": 0.91
}
```

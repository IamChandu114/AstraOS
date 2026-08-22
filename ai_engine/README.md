# AI Workload Prediction Engine

The AI engine predicts CPU spikes, overheating, abnormal memory growth, and inefficient workloads.

## Models

- LSTM interface for temporal workload prediction.
- Random Forest regressor for CPU and thermal forecasting.
- Isolation Forest for anomaly detection.
- Reinforcement-style action scorer for optimization decisions.

## Run

```bash
python predictor.py --demo --steps 30
python predictor.py --metrics ../benchmarks/demo_metrics.json
```

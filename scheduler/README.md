# Intelligent CPU Scheduler

This module creates optimization plans for CPU affinity, process priority, thread balancing, and memory-pressure handling.

It separates planning from privileged execution. By default it is dry-run only.

```bash
python optimizer.py --metrics ../benchmarks/demo_metrics.json
sudo python optimizer.py --metrics ../benchmarks/demo_metrics.json --apply
```

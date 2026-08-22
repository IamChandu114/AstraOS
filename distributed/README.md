# Distributed Edge Execution

Tracks real heterogeneous workload placement across configured nodes:

- Laptop
- Jetson Nano
- Raspberry Pi

The orchestrator measures real TCP heartbeat latency and allocates work only across online nodes. It does not create simulated nodes.

```bash
python orchestrator.py --nodes laptop=10.0.0.2:9100,jetson=10.0.0.3:9100,pi=10.0.0.4:9100
```

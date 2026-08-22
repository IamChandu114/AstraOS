# AstraOS Demo Checklist

## Start

Backend:

```powershell
cd C:\Users\Chand\OneDrive\Desktop\ASTRAOS
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 
```  
C:\Users\Chand\AppData\Local\Programs\Python\Python310\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 
Dashboard:

```powershell
cd C:\Users\Chand\OneDrive\Desktop\ASTRAOS\dashboard
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
Dashboard: http://127.0.0.1:5173
API Docs: http://127.0.0.1:8000/docs
Proof: http://127.0.0.1:8000/proof/live
```

## Verify

```powershell
python scripts/final_health_check.py
```

Check:

```text
http://127.0.0.1:8000/metrics
http://127.0.0.1:8000/predict
http://127.0.0.1:8000/predictive/alerts
http://127.0.0.1:8000/root-cause
http://127.0.0.1:8000/incidents
http://127.0.0.1:8000/reliability
http://127.0.0.1:8000/executive-summary
```


## Demo Order

1. Show `Dashboard`.
2. Show `CPU Intelligence`.
3. Show `Memory Optimizer`.
4. Show `AI Predictions`.
5. Show `Predictive Notification Center`.
6. Show `Prediction Timeline`.
7. Show `AstraOS Reliability Index`.
8. Show `AI Root Cause Analysis`.
9. Show `Incident Timeline`.
10. Show `Before vs After Proof`.
11. Show `Distributed Edge`.
12. Show `Proof Mode`.


## Chaos Demo


```powershell
Invoke-WebRequest -Method POST "http://127.0.0.1:8000/chaos/cpu?duration_seconds=90"
```

Then refresh/show:

```text
Live Infrastructure Logs
Incident Timeline
Predictive Notification Center
Distributed Edge
```

## Optimization Demo

Plan only:

```powershell
Invoke-WebRequest "http://127.0.0.1:8000/optimize"
```

Guarded apply:

```powershell
$env:ASTRAOS_ENABLE_APPLY="1"
Invoke-WebRequest -Method POST "http://127.0.0.1:8000/optimize?apply=true"
Invoke-WebRequest "http://127.0.0.1:8000/optimization/proof"
```



## One-Line Pitch

```text
AstraOS is an AI-native predictive operations platform that observes real system telemetry, predicts future failures, explains root causes, recommends safe optimizations, and verifies impact with proof.
```


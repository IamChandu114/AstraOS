from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.astraos.collector import TelemetryCollector
from backend.astraos.capability import host_capabilities
from backend.astraos.containers import ContainerAwareness
from backend.astraos.distributed_sim import DistributedFabric
from backend.astraos.digital_twin import DigitalTwin
from backend.astraos.ebpf import KernelObservability
from backend.astraos.events import EventStream
from backend.astraos.healing import SelfHealingEngine
from backend.astraos.incidents import IncidentTimelineEngine
from backend.astraos.nodes import NodeRegistry
from backend.astraos.policy import OptimizationPolicy
from backend.astraos.prediction import RealTelemetryPredictor
from backend.astraos.predictive_alerts import PredictiveAlertEngine
from backend.astraos.proof import ProofPackager
from backend.astraos.proof_engine import OptimizationProofEngine
from backend.astraos.profiler import Profiler
from backend.astraos.research import ResearchReportGenerator
from backend.astraos.root_cause import RootCauseAnalyzer
from backend.astraos.scheduler_sim import SchedulerSimulator
from backend.astraos.security import SecurityAnalyzer
from backend.astraos.storage import TelemetryStore
from backend.astraos.thermal import ThermalForecaster
from backend.astraos.training import AdaptiveTrainingPipeline
from backend.astraos.workload import WorkloadClassifier


TOKEN = os.getenv("ASTRAOS_TOKEN", "")
DB_PATH = os.getenv("ASTRAOS_DB_PATH", "data/astraos.db")
DEFAULT_CORS_ORIGINS = (
    "https://astra-os-mu.vercel.app",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)
CORS_ORIGINS = sorted({
    origin.strip()
    for origin in os.getenv("ASTRAOS_CORS_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS)).split(",")
    if origin.strip()
} | set(DEFAULT_CORS_ORIGINS))

app = FastAPI(
    title="AstraOS Runtime API",
    version="1.0.0",
    description="Production telemetry, prediction, and optimization API for AstraOS.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

collector = TelemetryCollector()
store = TelemetryStore(DB_PATH)
predictor = RealTelemetryPredictor()
policy = OptimizationPolicy()
nodes = NodeRegistry()
workloads = WorkloadClassifier()
thermal_forecaster = ThermalForecaster()
kernel = KernelObservability()
containers = ContainerAwareness()
healer = SelfHealingEngine()
security = SecurityAnalyzer()
scheduler_sim = SchedulerSimulator()
twin = DigitalTwin()
profiler = Profiler()
trainer = AdaptiveTrainingPipeline()
researcher = ResearchReportGenerator()
fabric = DistributedFabric()
events = EventStream()
proofs = ProofPackager()
root_causes = RootCauseAnalyzer()
incidents = IncidentTimelineEngine()
proof_engine = OptimizationProofEngine()
predictive_alerts = PredictiveAlertEngine()
history: deque[dict[str, Any]] = deque(maxlen=3600)
latest_prediction: dict[str, Any] | None = None
latest_distributed: dict[str, Any] | None = None
latest_optimization_result: dict[str, Any] | None = None
latest_predictive_alerts: dict[str, Any] | None = None
latest_incident_timeline: dict[str, Any] | None = None
pipeline_debug: deque[dict[str, Any]] = deque(maxlen=300)
rate_window: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=120))


def authenticate(authorization: str | None = Header(default=None), token: str | None = Query(default=None)) -> None:
    if not TOKEN:
        return
    supplied = token or ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization.split(" ", 1)[1].strip()
    if supplied != TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing AstraOS token")


def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.time()
    window = rate_window[client]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= int(os.getenv("ASTRAOS_RATE_LIMIT_PER_MINUTE", "600")):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    window.append(now)


async def sample_loop() -> None:
    global latest_prediction, latest_distributed, latest_predictive_alerts, latest_incident_timeline
    events.seed()
    while True:
        try:
            snapshot = await asyncio.to_thread(collector.collect)
            history.append(snapshot)
            await asyncio.to_thread(store.write_telemetry, snapshot)
            _debug_stage("telemetry", snapshot, "collector sampled host metrics")
            if len(history) >= 3:
                latest_prediction = await asyncio.to_thread(predictor.predict, list(history))
                await asyncio.to_thread(store.write_prediction, latest_prediction)
                _debug_stage("prediction", latest_prediction, "prediction engine produced live forecasts")
            latest_distributed = fabric.snapshot()
            latest = history[-1] if history else None
            rca = root_causes.analyze(latest, latest_prediction)
            latest_predictive_alerts = predictive_alerts.generate(list(history)[-240:], latest_prediction, rca)
            await asyncio.to_thread(store.write_predictive_alerts, latest_predictive_alerts)
            _debug_stage("risk", latest_predictive_alerts, "risk engine evaluated reliability and predictive alerts")
            _emit_risk_delta_events(latest_prediction, latest_predictive_alerts)
            _emit_predictive_alert_events(latest_predictive_alerts, latest_distributed)
            _debug_stage("notification", latest_predictive_alerts, "notification engine published dashboard/browser alert payload")
            _emit_runtime_events(snapshot, latest_prediction, latest_distributed)
            latest_incident_timeline = incidents.build(list(history)[-240:], latest_prediction, events.recent(120), rca)
            await asyncio.to_thread(store.write_incident, latest_incident_timeline)
            _debug_stage("timeline", latest_incident_timeline, "incident timeline generated and persisted")
        except Exception as exc:
            await asyncio.to_thread(store.write_action, "collector_error", {"error": str(exc), "timestamp": time.time()})
            events.emit("error", "astra-control-plane", f"Collector error: {exc}", "collector")
            _debug_stage("error", {"error": str(exc)}, "pipeline stage failed")
        await asyncio.sleep(float(os.getenv("ASTRAOS_SAMPLE_INTERVAL", "1.0")))


@app.on_event("startup")
async def startup() -> None:
    Path("data").mkdir(exist_ok=True)
    asyncio.create_task(sample_loop())

@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "AstraOS Runtime API",
        "status": "online",
        "version": "1.0.0",
        "message": "AstraOS backend is running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }

@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "samples": len(history), "auth_enabled": bool(TOKEN)}

@app.get("/status", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def status() -> dict[str, Any]:
    latest = history[-1] if history else None

    return {
        "status": "live" if latest else "warming_up",
        "samples": len(history),
        "auth_enabled": bool(TOKEN),
        "latest": latest,
        "prediction": latest_prediction,
        "predictive_alerts": latest_predictive_alerts,
        "distributed": latest_distributed or fabric.snapshot(),
        "incident_timeline": latest_incident_timeline,
    }

@app.get("/metrics", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def metrics(limit: int = 120) -> dict[str, Any]:
    if not history:
        return {"status": "warming_up", "history": []}
    return {"status": "live", "latest": history[-1], "history": list(history)[-max(1, min(limit, 1000)) :]}


@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket, token: str | None = None) -> None:
    if TOKEN and token != TOKEN:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            payload = {
                "type": "telemetry",
                "latest": history[-1] if history else None,
                "history": list(history)[-180:],
                "prediction": latest_prediction,
                "predictive_alerts": latest_predictive_alerts,
                "incident_timeline": latest_incident_timeline,
                "pipeline_debug": list(pipeline_debug)[-80:],
                "nodes": await nodes.heartbeat(),
                "distributed": latest_distributed or fabric.snapshot(),
                "events": events.recent(50),
            }
            _debug_stage("dashboard", payload, "websocket telemetry payload sent to dashboard")
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return


@app.get("/predict", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def predict() -> dict[str, Any]:
    prediction = predictor.predict(list(history))
    store.write_prediction(prediction)
    return prediction


@app.post("/optimize", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def optimize(apply: bool = False) -> dict[str, Any]:
    global latest_optimization_result
    if not history:
        raise HTTPException(status_code=503, detail="no live telemetry available yet")
    prediction = latest_prediction or predictor.predict(list(history))
    plan = policy.plan(history[-1], prediction)
    if apply:
        before = await asyncio.to_thread(collector.collect)
        result = await asyncio.to_thread(policy.apply, plan)
        await asyncio.sleep(1)
        after = await asyncio.to_thread(collector.collect)
        result["before"] = before
        result["after"] = after
        result["impact"] = _impact(before, after)
        result["proof"] = proof_engine.summarize(result, store.latest("benchmarks"))
        latest_optimization_result = result
    else:
        result = plan
    store.write_action("optimize_apply" if apply else "optimize_plan", result)
    events.emit("info", "astra-control-plane", "Optimization policy generated." if not apply else "Optimization apply request completed.", "optimization", apply=apply)
    return result


@app.get("/optimize", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def optimize_plan() -> dict[str, Any]:
    return await optimize(apply=False)


@app.get("/thermal", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def thermal() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up"}
    snapshot = history[-1]
    prediction = latest_prediction or predictor.predict(list(history))
    return {
        "status": "live",
        "thermal": snapshot.get("thermal"),
        "gpu": snapshot.get("gpu"),
        "forecast": prediction.get("thermal") if prediction else None,
        "thermal_forecast": thermal_forecaster.forecast(list(history)[-180:]),
    }


@app.get("/scheduler", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def scheduler() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up"}
    return {
        "status": "live",
        "cpu": history[-1].get("cpu"),
        "processes": history[-1].get("processes"),
        "plan": policy.plan(history[-1], latest_prediction),
        "simulation": scheduler_sim.compare(history[-1]),
    }


@app.get("/nodes", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def node_status() -> dict[str, Any]:
    real_nodes = await nodes.heartbeat()
    return {"real_edge_nodes": real_nodes, "distributed_fabric": latest_distributed or fabric.snapshot()}


@app.get("/distributed/status", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def distributed_status() -> dict[str, Any]:
    return latest_distributed or fabric.snapshot()


@app.websocket("/ws/distributed")
async def distributed_ws(websocket: WebSocket, token: str | None = None) -> None:
    if TOKEN and token != TOKEN:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "distributed", "distributed": latest_distributed or fabric.snapshot(), "events": events.recent(50)})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@app.get("/events", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def runtime_events(limit: int = 100) -> dict[str, Any]:
    return {"events": events.recent(limit)}


@app.get("/pipeline/debug", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def pipeline_debug_status(limit: int = 120) -> dict[str, Any]:
    return {"status": "live" if history else "warming_up", "debug": list(pipeline_debug)[-max(1, min(limit, 300)) :]}


@app.websocket("/ws/events")
async def events_ws(websocket: WebSocket, token: str | None = None) -> None:
    if TOKEN and token != TOKEN:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "events", "events": events.recent(80)})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@app.get("/workloads", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def workload_status() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up"}
    return workloads.classify(history[-1])


@app.get("/containers", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def container_status() -> dict[str, Any]:
    return await asyncio.to_thread(containers.inspect)


@app.get("/kernel/status", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def kernel_status() -> dict[str, Any]:
    return kernel.status()


@app.post("/kernel/sample", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def kernel_sample(seconds: int = 3) -> dict[str, Any]:
    return await asyncio.to_thread(kernel.sample, seconds)


@app.get("/thermal/forecast", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def thermal_forecast() -> dict[str, Any]:
    return thermal_forecaster.forecast(list(history)[-180:])


@app.get("/heal", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def healing_status() -> dict[str, Any]:
    return healer.evaluate(list(history)[-240:], latest_prediction)


@app.post("/heal", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def healing_plan(apply: bool = False) -> dict[str, Any]:
    evaluation = healer.evaluate(list(history)[-240:], latest_prediction)
    if not apply:
        return evaluation
    if not history:
        raise HTTPException(status_code=503, detail="no live telemetry available yet")
    plan = policy.plan(history[-1], latest_prediction)
    result = await asyncio.to_thread(policy.apply, plan)
    store.write_action("self_heal_apply", {"evaluation": evaluation, "result": result})
    return {"evaluation": evaluation, "result": result}


@app.get("/security", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def security_status() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up"}
    return security.analyze(history[-1], latest_prediction)


@app.get("/predictive/alerts", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def predictive_alert_status() -> dict[str, Any]:
    latest = history[-1] if history else None
    rca = root_causes.analyze(latest, latest_prediction)
    return latest_predictive_alerts or predictive_alerts.generate(list(history)[-240:], latest_prediction, rca)


@app.get("/reliability", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def reliability_status() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up", "reliability_index": {"score": 0, "trend": "warming"}}
    return {"status": "live", "reliability_index": predictive_alerts.reliability_index(history[-1], latest_prediction)}


@app.get("/executive-summary", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def executive_summary() -> dict[str, Any]:
    latest = history[-1] if history else None
    rca = root_causes.analyze(latest, latest_prediction)
    alerts = latest_predictive_alerts or predictive_alerts.generate(list(history)[-240:], latest_prediction, rca)
    return {"status": alerts.get("status"), "summary": alerts.get("executive_summary"), "alerts": alerts.get("alerts", []), "reliability_index": alerts.get("reliability_index")}


@app.get("/root-cause", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def root_cause() -> dict[str, Any]:
    latest = history[-1] if history else None
    return root_causes.analyze(latest, latest_prediction)


@app.get("/incidents", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def incident_timeline() -> dict[str, Any]:
    latest = history[-1] if history else None
    rca = root_causes.analyze(latest, latest_prediction)
    return latest_incident_timeline or incidents.build(list(history)[-240:], latest_prediction, events.recent(120), rca)


@app.get("/incidents/history", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def incident_history(limit: int = 100) -> dict[str, Any]:
    return {"incidents": store.history("incident_history", limit)}


@app.get("/optimization/proof", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def optimization_proof() -> dict[str, Any]:
    return proof_engine.summarize(latest_optimization_result, store.latest("benchmarks"))


@app.post("/optimize/rollback", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def optimize_rollback() -> dict[str, Any]:
    if not latest_optimization_result:
        raise HTTPException(status_code=404, detail="no optimization execution with rollback metadata is available")
    rollback_plan = latest_optimization_result.get("rollback_plan") or []
    result = await asyncio.to_thread(policy.rollback, rollback_plan)
    store.write_action("optimize_rollback", result)
    events.emit("info", "astra-control-plane", "Optimization rollback command completed.", "optimization")
    return result


@app.get("/scheduler/simulate", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def scheduler_compare() -> dict[str, Any]:
    if not history:
        return {"status": "warming_up"}
    return scheduler_sim.compare(history[-1])


@app.get("/digital-twin", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def digital_twin(horizon_seconds: int = 60) -> dict[str, Any]:
    return twin.project(list(history)[-240:], horizon_seconds)


@app.get("/profile/status", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def profile_status() -> dict[str, Any]:
    return profiler.status()


@app.post("/profile", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def profile(seconds: int = 5) -> dict[str, Any]:
    return await asyncio.to_thread(profiler.profile, seconds)


@app.post("/training/train", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def train_models() -> dict[str, Any]:
    result = await asyncio.to_thread(trainer.train, store.history("telemetry", 5000))
    store.write_action("model_training", result)
    return result


@app.get("/training/models", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def model_versions() -> dict[str, Any]:
    return {"models": trainer.versions()}


@app.get("/elite/status", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def elite_status() -> dict[str, Any]:
    latest = history[-1] if history else None
    scheduler = scheduler_sim.compare(latest) if latest else None
    healing = healer.evaluate(list(history)[-240:], latest_prediction)
    container_state = await asyncio.to_thread(containers.inspect)
    kernel_state = kernel.status()
    rca = root_causes.analyze(latest, latest_prediction)
    alert_state = latest_predictive_alerts or predictive_alerts.generate(list(history)[-240:], latest_prediction, rca)
    return {
        "status": "live" if latest else "warming_up",
        "workload": workloads.classify(latest) if latest else None,
        "thermal_forecast": thermal_forecaster.forecast(list(history)[-180:]),
        "healing": healing,
        "security": security.analyze(latest, latest_prediction) if latest else None,
        "scheduler_simulation": scheduler,
        "digital_twin": twin.project(list(history)[-240:], 60),
        "kernel_observability": kernel_state,
        "containers": container_state,
        "distributed": latest_distributed or fabric.snapshot(),
        "root_cause": rca,
        "predictive_alerts": alert_state,
        "reliability_index": alert_state.get("reliability_index"),
        "executive_summary": alert_state.get("executive_summary"),
        "incident_timeline": latest_incident_timeline or incidents.build(list(history)[-240:], latest_prediction, events.recent(120), rca),
        "optimization_proof": proof_engine.summarize(latest_optimization_result, store.latest("benchmarks")),
        "capabilities": host_capabilities(latest, kernel_state, container_state),
        "events": events.recent(30),
        "models": trainer.versions()[:5],
    }


@app.get("/proof/live", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def proof_live() -> dict[str, Any]:
    latest = history[-1] if history else None
    kernel_state = kernel.status()
    container_state = await asyncio.to_thread(containers.inspect)
    prediction = latest_prediction or (predictor.predict(list(history)) if history else None)
    plan = policy.plan(latest, prediction) if latest else None
    benchmark = store.latest("benchmarks")
    return proofs.build(
        latest,
        list(history),
        prediction,
        plan,
        latest_distributed or fabric.snapshot(),
        host_capabilities(latest, kernel_state, container_state),
        benchmark,
        events.recent(120),
    )


@app.get("/architecture", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def architecture() -> dict[str, Any]:
    return {
        "title": "AstraOS production architecture",
        "layers": [
            {"id": "collectors", "label": "Collectors", "items": ["psutil", "/proc", "sysfs", "nvidia-smi", "Docker", "kubectl", "perf/eBPF"]},
            {"id": "runtime", "label": "FastAPI Runtime", "items": ["/metrics", "/predict", "/optimize", "/proof/live", "WebSockets"]},
            {"id": "ai", "label": "AI Intelligence", "items": ["forecasting", "anomaly detection", "workload classification", "digital twin"]},
            {"id": "optimizer", "label": "Optimization Layer", "items": ["renice", "taskset/affinity", "cgroups", "memory pressure", "policy guardrails"]},
            {"id": "fabric", "label": "Distributed Fabric", "items": ["astra-node-1", "astra-node-2", "astra-node-3", "astra-node-4"]},
            {"id": "observability", "label": "Observability", "items": ["Prometheus", "Grafana", "Loki", "OpenTelemetry", "SQLite history"]},
            {"id": "ui", "label": "Control Surfaces", "items": ["dashboard", "proof mode", "architecture mode", "demo mode"]},
        ],
        "flows": [
            ["collectors", "runtime"],
            ["runtime", "ai"],
            ["ai", "optimizer"],
            ["optimizer", "fabric"],
            ["runtime", "observability"],
            ["runtime", "ui"],
        ],
    }


@app.post("/stress/{mode}", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def stress(mode: str, intensity: float = 1.0, duration_seconds: int = 90) -> dict[str, Any]:
    if mode not in {"cpu", "memory", "network", "thermal", "disk", "node_crash", "container_crash"}:
        raise HTTPException(status_code=400, detail="mode must be one of cpu, memory, network, thermal, disk, node_crash, container_crash")
    result = fabric.apply_stress(mode, intensity, duration_seconds)
    events.emit("warning", "astra-control-plane", f"{mode} chaos scenario activated.", "chaos", intensity=result["intensity"])
    return {"status": "activated", **result, "distributed": fabric.snapshot()}


@app.post("/chaos/{mode}", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def chaos(mode: str, intensity: float = 1.0, duration_seconds: int = 90) -> dict[str, Any]:
    return await stress(mode, intensity, duration_seconds)


@app.get("/benchmarks", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def benchmarks() -> dict[str, Any]:
    latest = store.latest("benchmarks")
    return latest or {
        "status": "no_real_benchmark_recorded",
        "message": "Run scripts/run_real_benchmark.py to capture a baseline and optimized report.",
        "metrics": [],
    }


@app.get("/logs", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def logs(limit: int = 100) -> dict[str, Any]:
    return {"logs": store.history("optimization_logs", limit)}


@app.get("/research-report", dependencies=[Depends(rate_limit), Depends(authenticate)])
async def research_report() -> dict[str, Any]:
    latest = history[-1] if history else None
    benchmark = store.latest("benchmarks")
    scheduler = scheduler_sim.compare(latest) if latest else None
    healing = healer.evaluate(list(history)[-240:], latest_prediction)
    return researcher.generate(latest, latest_prediction, benchmark, scheduler, healing)


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
async def prometheus() -> str:
    if not history:
        return "# AstraOS warming up\n"
    snap = history[-1]
    lines = [
        "# HELP astraos_cpu_usage_percent Current CPU usage percent",
        "# TYPE astraos_cpu_usage_percent gauge",
        f"astraos_cpu_usage_percent {snap.get('cpu', {}).get('usage_percent') or 0}",
        "# HELP astraos_memory_usage_percent Current memory usage percent",
        "# TYPE astraos_memory_usage_percent gauge",
        f"astraos_memory_usage_percent {snap.get('memory', {}).get('percent') or 0}",
        "# HELP astraos_process_total Current process count",
        "# TYPE astraos_process_total gauge",
        f"astraos_process_total {snap.get('processes', {}).get('total') or 0}",
    ]
    if latest_prediction:
        confidence = max(
            latest_prediction.get("cpu_spike", {}).get("confidence") or 0,
            latest_prediction.get("memory_pressure", {}).get("confidence") or 0,
            latest_prediction.get("power", {}).get("confidence") or 0,
        )
        lines.extend([
            "# HELP astraos_prediction_confidence Current maximum prediction confidence",
            "# TYPE astraos_prediction_confidence gauge",
            f"astraos_prediction_confidence {confidence}",
        ])
    temp = snap.get("thermal", {}).get("hottest_c")
    if temp is not None:
        lines.extend([
            "# HELP astraos_temperature_c Hottest detected temperature",
            "# TYPE astraos_temperature_c gauge",
            f"astraos_temperature_c {temp}",
        ])
    return "\n".join(lines) + "\n"


def _impact(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "cpu_delta_percent": round((after.get("cpu", {}).get("usage_percent") or 0) - (before.get("cpu", {}).get("usage_percent") or 0), 2),
        "memory_delta_percent": round((after.get("memory", {}).get("percent") or 0) - (before.get("memory", {}).get("percent") or 0), 2),
        "process_delta": int(after.get("processes", {}).get("total") or 0) - int(before.get("processes", {}).get("total") or 0),
        "thermal_delta_c": _nullable_delta(before.get("thermal", {}).get("hottest_c"), after.get("thermal", {}).get("hottest_c")),
    }


def _nullable_delta(before: Any, after: Any) -> float | None:
    if before is None or after is None:
        return None
    return round(float(after) - float(before), 2)


def _debug_stage(stage: str, payload: dict[str, Any] | None, message: str) -> None:
    payload = payload or {}
    entry = {
        "timestamp": time.time(),
        "time": time.strftime("%H:%M:%S"),
        "stage": stage,
        "message": message,
        "metrics": _debug_metrics(payload),
    }
    pipeline_debug.append(entry)


def _debug_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    latest = payload.get("latest") if payload.get("type") == "telemetry" else payload
    metrics = {}
    if "cpu" in latest or "memory" in latest:
        metrics.update({
            "cpu": latest.get("cpu", {}).get("usage_percent"),
            "memory": latest.get("memory", {}).get("percent"),
            "disk": latest.get("disk", {}).get("root_percent"),
            "network_rx_bps": latest.get("network", {}).get("bytes_recv_per_sec"),
            "thermal": latest.get("thermal", {}).get("hottest_c"),
        })
    if "memory_pressure" in latest:
        forecast = latest.get("memory_pressure", {})
        metrics.update({
            "memory_current": forecast.get("current"),
            "memory_forecast_60s": forecast.get("forecast_60s"),
            "memory_risk": forecast.get("risk"),
            "memory_risk_score": forecast.get("risk_score"),
            "memory_expected_failure": forecast.get("expected_failure_label"),
        })
    if "reliability_index" in latest:
        metrics.update({
            "reliability_score": latest.get("reliability_index", {}).get("score"),
            "active_alerts": len(latest.get("alerts", [])),
            "primary_alert": (latest.get("alerts") or [{}])[0].get("title"),
        })
    if "incident_id" in latest:
        metrics.update({
            "incident_id": latest.get("incident_id"),
            "incident_severity": latest.get("severity"),
            "timeline_events": len(latest.get("timeline", [])),
        })
    return {key: value for key, value in metrics.items() if value is not None}


_last_risk_scores: dict[str, float] = {}


def _emit_risk_delta_events(prediction: dict[str, Any] | None, alert_state: dict[str, Any] | None) -> None:
    if not prediction:
        return
    for key in ("cpu_spike", "memory_pressure", "thermal", "power"):
        forecast = prediction.get(key, {})
        score = float(forecast.get("risk_score") or 0)
        previous = _last_risk_scores.get(key, 0.0)
        _last_risk_scores[key] = score
        if score >= previous + 5 or forecast.get("risk") in {"warning", "critical"} and previous < 72 <= score:
            events.emit(
                "critical" if score >= 90 else "warning" if score >= 72 else "info",
                "astra-risk-engine",
                f"{key.replace('_', ' ')} risk increased from {round(previous, 1)} to {round(score, 1)}.",
                "risk",
                metric=key,
                risk_score=score,
                current=forecast.get("current"),
                forecast_60s=forecast.get("forecast_60s"),
                confidence=forecast.get("confidence"),
                expected_failure_time=forecast.get("expected_failure_time"),
            )
    for alert in (alert_state or {}).get("alerts", [])[:3]:
        if alert.get("affected_resource") == "memory":
            bucket_key = f"notification:{alert.get('affected_resource')}:{int(time.time() // 60)}"
            if _last_event_bucket.get(bucket_key):
                continue
            _last_event_bucket[bucket_key] = 1
            events.emit(
                "warning" if alert.get("risk_level") != "critical" else "critical",
                "astra-notification-center",
                f"User notification ready: {alert.get('message')}",
                "notification",
                alert_id=alert.get("alert_id"),
                confidence=alert.get("confidence_score"),
                expected_failure_time=alert.get("expected_failure_time"),
            )


_last_event_bucket: dict[str, int] = {}


def _emit_runtime_events(snapshot: dict[str, Any], prediction: dict[str, Any] | None, distributed: dict[str, Any]) -> None:
    now_bucket = int(time.time() // 10)
    cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
    memory = float(snapshot.get("memory", {}).get("percent") or 0)
    if cpu > 80 and _last_event_bucket.get("cpu") != now_bucket:
        _last_event_bucket["cpu"] = now_bucket
        events.emit("warning", snapshot.get("host", {}).get("hostname", "host"), f"CPU pressure detected at {cpu:.1f}%.", "telemetry", metric="cpu", value=cpu)
    if memory > 82 and _last_event_bucket.get("memory") != now_bucket:
        _last_event_bucket["memory"] = now_bucket
        events.emit("warning", snapshot.get("host", {}).get("hostname", "host"), f"Memory pressure reached {memory:.1f}%.", "telemetry", metric="memory", value=memory)
    if prediction:
        for key in ("cpu_spike", "memory_pressure", "thermal"):
            risk = prediction.get(key, {}).get("risk")
            if risk in {"warning", "critical"} and _last_event_bucket.get(key) != now_bucket:
                _last_event_bucket[key] = now_bucket
                events.emit("info", "astra-ai-engine", f"{key.replace('_', ' ')} forecast reports {risk} risk.", "ai", confidence=prediction.get(key, {}).get("confidence"))


_last_predictive_alert_bucket: dict[str, int] = {}


def _emit_predictive_alert_events(alert_state: dict[str, Any] | None, distributed: dict[str, Any] | None = None) -> None:
    if not alert_state:
        return
    now_bucket = int(time.time() // 30)
    for alert in alert_state.get("alerts", [])[:5]:
        key = str(alert.get("affected_resource"))
        if _last_predictive_alert_bucket.get(key) == now_bucket:
            continue
        _last_predictive_alert_bucket[key] = now_bucket
        events.emit(
            "critical" if alert.get("risk_level") == "critical" else "warning",
            "astra-predictive-engine",
            alert.get("message") or alert.get("title") or "Predictive alert generated.",
            "predictive",
            alert_id=alert.get("alert_id"),
            confidence=alert.get("confidence_score"),
            expected_failure_time=alert.get("expected_failure_time"),
            time_remaining_minutes=alert.get("time_remaining_minutes"),
        )
    for event in (distributed or {}).get("orchestration_events", [])[:3]:
        key = f"migration:{event['source']}:{now_bucket}"
        if _last_event_bucket.get(key) != now_bucket:
            _last_event_bucket[key] = now_bucket
            events.emit("info", event["source"], f"AI recommends migrating workload to {event['target']}.", "orchestration", confidence=event.get("confidence"), target=event.get("target"))

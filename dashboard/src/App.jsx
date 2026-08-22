import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import {
  Activity,
  BarChart3,
  BatteryCharging,
  BrainCircuit,
  Cpu,
  Gauge,
  LayoutDashboard,
  MemoryStick,
  Network,
  RadioTower,
  Settings,
  ShieldCheck,
  Sparkles,
  Terminal,
  Thermometer,
  Zap
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_ASTRAOS_API_URL || 'http://127.0.0.1:8000';
const API_TOKEN = import.meta.env.VITE_ASTRAOS_TOKEN || '';

const navItems = [
  [LayoutDashboard, 'Dashboard', 'dashboard-overview'],
  [Cpu, 'CPU Intelligence', 'cpu-intelligence'],
  [Thermometer, 'Thermal Engine', 'thermal-engine'],
  [MemoryStick, 'Memory Optimizer', 'memory-optimizer'],
  [BrainCircuit, 'AI Predictions', 'ai-predictions'],
  [RadioTower, 'Distributed Edge', 'distributed-edge'],
  [Activity, 'Process Monitor', 'process-monitor'],
  [BarChart3, 'Benchmarks', 'benchmarks'],
  [Terminal, 'Logs', 'logs'],
  [Settings, 'Settings', 'settings']
];

function apiUrl(path) {
  return `${API_BASE}${path}${API_TOKEN ? `${path.includes('?') ? '&' : '?'}token=${encodeURIComponent(API_TOKEN)}` : ''}`;
}

function wsUrl() {
  const url = new URL(API_BASE);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/ws/telemetry';
  if (API_TOKEN) url.searchParams.set('token', API_TOKEN);
  return url.toString();
}

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function useLiveTelemetry() {
  const [state, setState] = useState({
    status: 'CONNECTING',
    latest: null,
    history: [],
    prediction: null,
    predictiveAlerts: null,
    incidentTimeline: null,
    pipelineDebug: [],
    nodes: null,
    distributed: null,
    events: [],
    error: null
  });

  useEffect(() => {
    let closed = false;
    let socket;
    let fallbackTimer;

    async function pollMetrics() {
      try {
        const response = await fetch(apiUrl('/metrics?limit=180'), {
          headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!closed) {
          setState((previous) => ({
            ...previous,
            status: payload.status === 'live' ? 'REST LIVE' : 'WARMING UP',
            latest: payload.latest || null,
            history: payload.history || [],
            error: null
          }));
        }
      } catch (error) {
        if (!closed) {
          setState((previous) => ({ ...previous, status: 'OFFLINE', error: error.message }));
        }
      }
    }

    try {
      socket = new WebSocket(wsUrl());
      socket.onopen = () => setState((previous) => ({ ...previous, status: 'WEBSOCKET LIVE', error: null }));
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        setState({
          status: 'WEBSOCKET LIVE',
          latest: payload.latest,
          history: payload.history || [],
          prediction: payload.prediction,
          predictiveAlerts: payload.predictive_alerts,
          incidentTimeline: payload.incident_timeline,
          pipelineDebug: payload.pipeline_debug || [],
          nodes: payload.nodes,
          distributed: payload.distributed,
          events: payload.events || [],
          error: null
        });
      };
      socket.onerror = () => {
        setState((previous) => ({ ...previous, status: 'REST FALLBACK', error: 'WebSocket unavailable' }));
        pollMetrics();
        fallbackTimer = setInterval(pollMetrics, 1500);
      };
      socket.onclose = () => {
        if (!closed) {
          setState((previous) => ({ ...previous, status: 'REST FALLBACK' }));
          pollMetrics();
          fallbackTimer = setInterval(pollMetrics, 1500);
        }
      };
    } catch (error) {
      setState((previous) => ({ ...previous, status: 'REST FALLBACK', error: error.message }));
      pollMetrics();
      fallbackTimer = setInterval(pollMetrics, 1500);
    }

    return () => {
      closed = true;
      if (fallbackTimer) clearInterval(fallbackTimer);
      if (socket) socket.close();
    };
  }, []);

  return state;
}

function useBenchmarks() {
  const [benchmarks, setBenchmarks] = useState({ metrics: [], status: 'loading' });
  useEffect(() => {
    let closed = false;
    async function load() {
      try {
        const response = await fetch(apiUrl('/benchmarks'), {
          headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}
        });
        const payload = await response.json();
        if (!closed) setBenchmarks(payload);
      } catch (error) {
        if (!closed) setBenchmarks({ status: 'offline', message: error.message, metrics: [] });
      }
    }
    load();
    const timer = setInterval(load, 10000);
    return () => {
      closed = true;
      clearInterval(timer);
    };
  }, []);
  return benchmarks;
}

function useEliteStatus() {
  const [elite, setElite] = useState({ status: 'loading' });
  useEffect(() => {
    let closed = false;
    async function load() {
      try {
        const response = await fetch(apiUrl('/elite/status'), {
          headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}
        });
        const payload = await response.json();
        if (!closed) setElite(payload);
      } catch (error) {
        if (!closed) setElite({ status: 'offline', error: error.message });
      }
    }
    load();
    const timer = setInterval(load, 5000);
    return () => {
      closed = true;
      clearInterval(timer);
    };
  }, []);
  return elite;
}

function useProof() {
  const [proof, setProof] = useState({ status: 'loading' });
  useEffect(() => {
    let closed = false;
    async function load() {
      try {
        const response = await fetch(apiUrl('/proof/live'), {
          headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}
        });
        const payload = await response.json();
        if (!closed) setProof(payload);
      } catch (error) {
        if (!closed) setProof({ status: 'offline', error: error.message });
      }
    }
    load();
    const timer = setInterval(load, 2500);
    return () => {
      closed = true;
      clearInterval(timer);
    };
  }, []);
  return proof;
}

function useArchitecture() {
  const [architecture, setArchitecture] = useState({ layers: [], flows: [] });
  useEffect(() => {
    let closed = false;
    async function load() {
      try {
        const response = await fetch(apiUrl('/architecture'), {
          headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}
        });
        const payload = await response.json();
        if (!closed) setArchitecture(payload);
      } catch (error) {
        if (!closed) setArchitecture({ layers: [], flows: [], error: error.message });
      }
    }
    load();
    return () => {
      closed = true;
    };
  }, []);
  return architecture;
}

function useBrowserPredictiveNotifications(alertState) {
  useEffect(() => {
    const alerts = alertState?.alerts || [];
    if (!alerts.length || typeof window === 'undefined' || !('Notification' in window)) return;
    function send(alert) {
      const key = `astraos-alert-${alert.alert_id}`;
      if (sessionStorage.getItem(key)) return;
      if (Notification.permission === 'granted') {
        sessionStorage.setItem(key, 'sent');
        new Notification(alert.title || 'AstraOS Predictive Alert', {
          body: `${alert.message || 'AstraOS predicted a future runtime issue.'} Confidence ${Math.round(Number(alert.confidence_score || 0) * 100)}%.`,
          tag: alert.alert_id,
          requireInteraction: alert.risk_level === 'critical'
        });
      }
    }
    if (Notification.permission === 'default') {
      Notification.requestPermission().then((permission) => {
        if (permission === 'granted') alerts.slice(0, 3).forEach(send);
      });
    } else {
      alerts.slice(0, 3).forEach(send);
    }
  }, [alertState]);
}

function chartPoint(snapshot) {
  const gpuPower = (snapshot?.gpu?.devices || []).reduce((sum, device) => sum + Number(device.power_watts || 0), 0);
  const cpu = Number(snapshot?.cpu?.usage_percent || 0);
  return {
    time: snapshot ? new Date(snapshot.timestamp * 1000).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' }) : '',
    cpu,
    memory: Number(snapshot?.memory?.percent || 0),
    temp: Number(snapshot?.thermal?.hottest_c || snapshot?.gpu?.devices?.[0]?.temperature_c || 0),
    power: Number((gpuPower + cpu * 0.22).toFixed(2)),
    processes: Number(snapshot?.processes?.total || 0),
    net: Number(((snapshot?.network?.bytes_recv_per_sec || 0) / 1024).toFixed(2)),
    disk: Number((((snapshot?.disk?.read_bytes_per_sec || 0) + (snapshot?.disk?.write_bytes_per_sec || 0)) / 1024).toFixed(2))
  };
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return 'Host metric not reported';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Number(bytes);
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatValue(value, suffix = '') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'Sensor adapter inactive';
  return `${value}${suffix}`;
}

function riskText(forecast) {
  if (!forecast) return 'Waiting for samples';
  return `${forecast.risk || 'unknown'} | ${formatValue(forecast.forecast_6s, '')}`;
}

function Logo() {
  return (
    <div className="brand-lockup">
      <div className="astra-glyph"><span /><span /><span /></div>
      <div>
        <strong>AstraOS</strong>
        <small>Real-Time AI Systems Control Center</small>
      </div>
    </div>
  );
}

function TopNav({ clock, telemetry }) {
  const nodes = telemetry.nodes?.nodes || [];
  const onlineNodes = nodes.filter((node) => node.online).length;
  const mode = telemetry.prediction?.recommendations?.[0] || 'observe';
  return (
    <header className="top-nav">
      <Logo />
      <div className="nav-status-grid">
        <StatusPill label="System" value={telemetry.latest ? 'ONLINE' : 'WARMING'} tone="cyan" />
        <StatusPill label="AI Engine" value={telemetry.prediction?.status || 'COLLECTING'} tone="purple" />
        <StatusPill label="Devices" value={`${onlineNodes}/${nodes.length} LINKED`} tone="blue" />
        <StatusPill label="Mode" value={mode.replaceAll('_', ' ').toUpperCase()} tone="green" />
        <StatusPill label="Stream" value={telemetry.status} tone="orange" />
      </div>
      <div className="clock">{clock}</div>
    </header>
  );
}

function StatusPill({ label, value, tone }) {
  return (
    <div className={`status-pill ${tone}`}>
      <span />
      <small>{label}</small>
      <b>{value}</b>
    </div>
  );
}

function Sidebar({ activeSection, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-scan" />
      {navItems.map(([Icon, label, target]) => (
        <button
          key={label}
          className={activeSection === target ? 'active' : ''}
          type="button"
          title={label}
          onClick={() => onNavigate(target)}
        >
          <Icon size={18} />
          <span>{label}</span>
        </button>
      ))}
    </aside>
  );
}

function Panel({ children, className = '', delay = 0, id }) {
  return (
    <motion.section
      id={id}
      className={`glass-panel ${className}`}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay }}
    >
      {children}
    </motion.section>
  );
}

function PanelHeader({ icon: Icon, eyebrow, title, action }) {
  return (
    <div className="panel-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2><Icon size={18} /> {title}</h2>
      </div>
      {action && <b>{action}</b>}
    </div>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

function OverviewHero({ latest, prediction, id }) {
  const cpu = latest?.cpu?.usage_percent;
  const temp = latest?.thermal?.hottest_c ?? latest?.gpu?.devices?.[0]?.temperature_c;
  const memory = latest?.memory?.percent;
  const gpuPower = (latest?.gpu?.devices || []).reduce((sum, device) => sum + Number(device.power_watts || 0), 0);
  const power = latest ? (gpuPower + Number(cpu || 0) * 0.22).toFixed(1) : null;
  return (
    <Panel id={id} className="overview-panel" delay={0.05}>
      <div className="hologram-core">
        <div className="orbital-ring r1" />
        <div className="orbital-ring r2" />
        <div className="orbital-ring r3" />
        <BrainCircuit size={70} />
      </div>
      <div className="overview-copy">
        <span className="eyebrow">Live Host Runtime Layer</span>
        <h1>{latest ? 'Real Telemetry Optimization Console' : 'Waiting For Live Telemetry'}</h1>
        <p>{latest ? `Host ${latest.host.hostname} is streaming actual CPU, memory, process, disk, network, thermal, GPU, and battery metrics when the host exposes those adapters.` : 'Start the AstraOS API server to stream real host telemetry into this dashboard.'}</p>
        {prediction?.workload_class && <p className="workload-class">Workload classification: <b>{prediction.workload_class.replaceAll('_', ' ')}</b></p>}
      </div>
      <div className="hero-metrics">
        <MetricChip icon={Cpu} label="CPU Load" value={formatValue(cpu, '%')} />
        <MetricChip icon={Thermometer} label="Thermal" value={formatValue(temp, ' C')} alert={Number(temp) > 80} />
        <MetricChip icon={MemoryStick} label="Memory" value={formatValue(memory, '%')} alert={Number(memory) > 82} />
        <MetricChip icon={Zap} label="Power Estimate" value={formatValue(power, ' W')} />
      </div>
    </Panel>
  );
}

function MetricChip({ icon: Icon, label, value, alert = false }) {
  return (
    <div className={`metric-chip ${alert ? 'alert' : ''}`}>
      <Icon size={20} />
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function CPUIntelligence({ data, latest, prediction, id }) {
  const cores = latest?.cpu?.per_core_percent || [];
  const topProcesses = (latest?.processes?.top || []).filter((proc) => Number(proc.pid || 0) > 1 && !['system idle process', 'system'].includes(String(proc.name || '').toLowerCase()));
  return (
    <Panel id={id} className="cpu-panel" delay={0.1}>
      <PanelHeader icon={Cpu} eyebrow="Panel 01" title="CPU Intelligence" action={riskText(prediction?.cpu_spike)} />
      {!latest ? <EmptyState message="CPU collector is warming up and waiting for host samples." /> : (
        <>
          <div className="cpu-layout">
            <div className="chart-shell">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="cpuGlow" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#00e7ff" stopOpacity={0.75} />
                      <stop offset="100%" stopColor="#6f4cff" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(132, 220, 255, 0.12)" vertical={false} />
                  <XAxis dataKey="time" stroke="#7fa4b8" tickLine={false} axisLine={false} />
                  <YAxis stroke="#7fa4b8" tickLine={false} axisLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="cpu" stroke="#00e7ff" strokeWidth={3} fill="url(#cpuGlow)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="core-grid">
              {cores.map((load, index) => (
                <div className={`core-cell ${index < Math.ceil(cores.length / 2) ? 'performance' : 'efficiency'}`} key={index}>
                  <b>C{index}</b>
                  <span style={{ height: `${Math.max(4, load)}%` }} />
                  <small>{formatValue(load, '%')}</small>
                </div>
              ))}
            </div>
          </div>
          <div className="allocation-strip">
            {topProcesses.slice(0, 3).map((proc, index) => (
              <span key={`${proc.pid}-${proc.name}`}>Core {index} {'->'} {proc.name} PID {proc.pid}</span>
            ))}
          </div>
        </>
      )}
    </Panel>
  );
}

function ThermalEngine({ data, latest, prediction, id }) {
  const sensors = latest?.thermal?.sensors || [];
  const hottest = latest?.thermal?.hottest_c ?? latest?.gpu?.devices?.[0]?.temperature_c;
  return (
    <Panel id={id} className="thermal-engine" delay={0.15}>
      <PanelHeader icon={Thermometer} eyebrow="Panel 02" title="Thermal Intelligence" action={riskText(prediction?.thermal)} />
      {!latest ? <EmptyState message="Thermal collector is warming up. On Windows or unsupported hardware, AstraOS reports thermal adapter state explicitly." /> : (
        <>
          <div className="thermal-layout">
            <div className="thermal-chip">
              <div className="thermal-pulse" style={{ opacity: hottest ? Math.min(0.9, Number(hottest) / 100) : 0.2 }} />
              {(sensors.length ? sensors : [{ label: 'Thermal sensor adapter inactive on this host', current_c: 0 }]).slice(0, 25).map((sensor, index) => (
                <i key={`${sensor.label}-${index}`} title={`${sensor.label}: ${sensor.current_c ?? 'host sensor not reported'} C`} />
              ))}
            </div>
            <div className="thermal-readout">
              <MetricChip icon={Thermometer} label="Current Temp" value={formatValue(hottest, ' C')} alert={Number(hottest) > 80} />
              <MetricChip icon={Gauge} label="Forecast" value={prediction?.thermal?.forecast_6s ? `${prediction.thermal.forecast_6s} C` : 'Warming'} />
              <MetricChip icon={ShieldCheck} label="Sensors" value={`${sensors.length}`} />
            </div>
          </div>
          <ResponsiveContainer width="100%" height={96}>
            <LineChart data={data}>
              <Line type="monotone" dataKey="temp" stroke="#ff8a2a" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="power" stroke="#b967ff" strokeWidth={2} dot={false} />
              <Tooltip content={<ChartTooltip />} />
            </LineChart>
          </ResponsiveContainer>
        </>
      )}
    </Panel>
  );
}

function MemoryEngine({ latest, prediction, id }) {
  const blocks = latest?.memory?.fragmentation || [];
  return (
    <Panel id={id} className="memory-panel" delay={0.2}>
      <PanelHeader icon={MemoryStick} eyebrow="Panel 03" title="Memory Engine" action={riskText(prediction?.memory_pressure)} />
      {!latest ? <EmptyState message="Memory collector is warming up and waiting for host samples." /> : (
        <>
          <div className="ram-bars">
            {blocks.map((value, index) => (
              <span key={index} style={{ height: `${Math.max(4, value)}%` }} className={value > 80 ? 'hot' : value < 45 ? 'cool' : ''} />
            ))}
          </div>
          <div className="fragment-grid">
            {blocks.concat(blocks).slice(0, 42).map((value, index) => <i key={index} className={value < 50 ? 'compressed' : ''} />)}
          </div>
          <div className="memory-stats">
            <span>RAM Used <b>{formatBytes(latest.memory.used_bytes)} / {formatBytes(latest.memory.total_bytes)}</b></span>
            <span>Cache <b>{formatBytes(latest.memory.cached_bytes)}</b></span>
            <span>Swap <b>{formatValue(latest.swap.percent, '%')}</b></span>
          </div>
        </>
      )}
    </Panel>
  );
}

function PowerOptimization({ data, latest, prediction }) {
  const gpuPower = (latest?.gpu?.devices || []).reduce((sum, device) => sum + Number(device.power_watts || 0), 0);
  const cpuProxy = Number(latest?.cpu?.usage_percent || 0) * 0.22;
  const power = latest ? (gpuPower + cpuProxy).toFixed(1) : null;
  return (
    <Panel className="power-panel" delay={0.25}>
      <PanelHeader icon={BatteryCharging} eyebrow="Panel 04" title="Power Optimization" action={riskText(prediction?.power)} />
      {!latest ? <EmptyState message="Power collector is warming up. GPU/battery adapters activate when host hardware exposes them." /> : (
        <>
          <div className="power-grid">
            <div className="energy-core">
              <Zap size={52} />
              <strong>{formatValue(power, ' W')}</strong>
              <small>CPU/GPU power estimate from live telemetry</small>
            </div>
            <div className="power-stats">
              <span>Battery <b>{latest.battery.available ? `${latest.battery.percent}% ${latest.battery.power_plugged ? 'plugged' : 'discharging'}` : 'Battery telemetry not reported by host'}</b></span>
              <span>GPU Power <b>{latest.gpu.available ? `${gpuPower.toFixed(1)} W` : 'GPU telemetry adapter inactive on current hardware'}</b></span>
              <span>CPU Proxy <b>{cpuProxy.toFixed(1)} W</b></span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={118}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="powerGlow" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#4dff88" stopOpacity={0.7} />
                  <stop offset="100%" stopColor="#4dff88" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="power" stroke="#4dff88" fill="url(#powerGlow)" strokeWidth={3} />
              <Tooltip content={<ChartTooltip />} />
            </AreaChart>
          </ResponsiveContainer>
        </>
      )}
    </Panel>
  );
}

function DecisionPanel({ prediction, telemetry, id }) {
  const logs = useMemo(() => {
    if (!prediction) return ['Waiting for live AI prediction samples from the backend.'];
    const rows = [
      `Workload classified as ${prediction.workload_class}`,
      `CPU forecast ${prediction.cpu_spike?.forecast_6s ?? 'unknown'}% (${prediction.cpu_spike?.risk ?? 'unknown'})`,
      `Thermal forecast ${prediction.thermal?.forecast_6s ?? 'host thermal adapter inactive'} C (${prediction.thermal?.risk ?? 'unknown'})`,
      `Memory forecast ${prediction.memory_pressure?.forecast_6s ?? 'unknown'}% (${prediction.memory_pressure?.risk ?? 'unknown'})`,
      `Anomaly status ${prediction.anomaly?.is_anomaly ? 'detected' : 'normal'} score ${prediction.anomaly?.score ?? 0}`,
      `Recommended actions: ${(prediction.recommendations || []).join(', ')}`
    ];
    if (telemetry.error) rows.push(`Stream notice: ${telemetry.error}`);
    return rows;
  }, [prediction, telemetry.error]);

  return (
    <Panel id={id} className="decision-panel" delay={0.1}>
      <PanelHeader icon={BrainCircuit} eyebrow="AI Command Center" title="Decision Engine" action={prediction?.sample_count ? `${prediction.sample_count} samples` : 'warming'} />
      <div className="terminal-log">
        {logs.map((log, index) => (
          <motion.p
            key={`${log}-${index}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
          >
            <span>[{String(index + 1).padStart(2, '0')}]</span> {log}
          </motion.p>
        ))}
        <p className="typing"><span /> ASTRA is reading the next real telemetry window</p>
      </div>
    </Panel>
  );
}

function AssistantPanel({ prediction, alertState }) {
  const copilot = alertState?.copilot;
  const text = copilot
    ? `${copilot.answer}. Recommended fix: ${copilot.recommended_fix}. Expected improvement: ${copilot.expected_improvement}.`
    : prediction?.recommendations?.length
      ? `I recommend ${prediction.recommendations.map((item) => item.replaceAll('_', ' ')).join(', ')} based on current host telemetry.`
      : 'I am waiting for enough real telemetry to produce an optimization recommendation.';
  return (
    <Panel className="assistant-panel" delay={0.18}>
      <PanelHeader icon={Sparkles} eyebrow="ASTRA AI" title="Operations Copilot" action={copilot ? `confidence ${Math.round(Number(copilot.confidence || 0) * 100)}%` : undefined} />
      <div className="assistant-orb"><BrainCircuit size={46} /></div>
      <blockquote>{text}</blockquote>
      <div className="assistant-actions">
        {(copilot?.contributors?.length ? copilot.contributors : (prediction?.recommendations || ['collecting_live_samples'])).slice(0, 4).map((item) => (
          <span key={item.pid || item}>
            {typeof item === 'string' ? item.replaceAll('_', ' ') : `${item.name}: CPU ${item.cpu_percent}% / MEM ${item.memory_percent}%`}
          </span>
        ))}
      </div>
    </Panel>
  );
}

function Recommendations({ latest, prediction }) {
  const top = latest?.processes?.top || [];
  const rows = [
    ['CPU scheduling', prediction?.cpu_spike?.risk || 'warming'],
    ['Thermal balancing', prediction?.thermal?.risk || 'sensor dependent'],
    ['Memory pressure', prediction?.memory_pressure?.risk || 'warming'],
    ['Top process', top[0] ? `${top[0].name} (${top[0].cpu_percent}%)` : 'unavailable']
  ];
  return (
    <Panel className="recommend-panel" delay={0.26}>
      <PanelHeader icon={ShieldCheck} eyebrow="Optimization Queue" title="Recommendations" />
      {rows.map(([label, text]) => (
        <div className="recommendation" key={label}>
          <b>{label}</b>
          <span>{text}</span>
        </div>
      ))}
    </Panel>
  );
}

function ProcessMonitorPanel({ latest, id }) {
  const processes = (latest?.processes?.top || [])
    .filter((proc) => Number(proc.pid || 0) > 1)
    .slice(0, 8);

  return (
    <Panel id={id} className="process-panel" delay={0.28}>
      <PanelHeader icon={Activity} eyebrow="Process Monitor" title="Live Host Process Table" action={latest ? `${latest.processes?.total || 0} processes` : 'warming'} />
      {processes.length ? (
        <div className="process-table">
          <div className="process-row process-head">
            <span>Process</span>
            <span>PID</span>
            <span>CPU</span>
            <span>Memory</span>
            <span>Policy View</span>
          </div>
          {processes.map((proc, index) => (
            <div className="process-row" key={`${proc.pid}-${proc.name}-${index}`}>
              <span><b>{proc.name || 'process'}</b><small>{proc.status || 'runtime state reported by host'}</small></span>
              <span>{proc.pid}</span>
              <span>{formatValue(proc.cpu_percent, '%')}</span>
              <span>{formatBytes(proc.memory_bytes ?? proc.memory_rss_bytes ?? proc.rss_bytes)}</span>
              <span>{Number(proc.cpu_percent || 0) > 25 ? 'priority candidate' : 'observe'}</span>
            </div>
          ))}
        </div>
      ) : <EmptyState message="Process collector is warming up and waiting for host process samples." />}
    </Panel>
  );
}

function EdgeExecution({ nodes, id }) {
  const realNodes = nodes?.real_edge_nodes?.nodes || [];
  const list = realNodes.length > 0 ? realNodes : (nodes?.distributed_fabric?.nodes || nodes?.nodes || []);
  const cluster = realNodes.length > 0 ? null : nodes?.distributed_fabric;
  const hasNodes = list.length > 0;
  const onlineCount = list.filter((node) => node.online || node.status === 'online').length;

  return (
    <Panel id={id} className="edge-panel" delay={0.3}>
      <PanelHeader
        icon={RadioTower}
        eyebrow="Panel 06"
        title="Distributed Edge Execution"
        action={
          hasNodes
            ? (realNodes.length > 0 ? `STATUS: CONNECTED` : (cluster ? `${cluster.online}/${cluster.node_count} synchronized` : `${onlineCount} LIVE EDGE NODE${onlineCount !== 1 ? 'S' : ''}`))
            : 'STATUS: STANDBY'
        }
      />
      {hasNodes ? (
        <div className="edge-map">
          {list.length > 1 && (
            <svg viewBox="0 0 100 100" preserveAspectRatio="none">
              {list.slice(1).map((_, index) => <line key={index} x1="50" y1="22" x2={index % 2 ? 75 : 25} y2="70" />)}
            </svg>
          )}
          {list.map((node, index) => (
            <div className="edge-node" key={node.name} style={{ left: `${index === 0 ? 50 : index % 2 ? 75 : 25}%`, top: `${index === 0 ? 22 : 70}%` }}>
              <RadioTower size={20} />
              <b>{node.telemetry?.name || node.name}</b>
              <small>{node.telemetry?.hostname ? `${node.telemetry.hostname} / ${node.telemetry.role || 'Edge Worker'}` : (node.status || (node.online ? 'online' : 'offline'))}</small>
              
              {node.telemetry ? (
                <div className="edge-node-telemetry">
                  <div className="telemetry-row"><span>CPU</span><span>{node.telemetry.cpu_percent ?? '—'}%</span></div>
                  <div className="telemetry-row"><span>MEMORY</span><span>{node.telemetry.memory_percent ?? '—'}%</span></div>
                  <div className="telemetry-row"><span>NETWORK</span><span>{node.telemetry.network?.bytes_recv ? formatBytes(node.telemetry.network.bytes_recv) : '—'}</span></div>
                  <div className="telemetry-row"><span>UPTIME</span><span>{node.telemetry.uptime_seconds ?? '—'}s</span></div>
                  <div className="telemetry-row"><span>LATENCY</span><span>{node.latency_ms ?? '—'} ms</span></div>
                  <div className="telemetry-connected">● ONLINE</div>
                </div>
              ) : (
                <span>{node.health_score ? `health ${node.health_score}` : node.latency_ms ? `${node.latency_ms} ms` : node.error || 'heartbeat pending'}</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="edge-standby">
          <div className="edge-standby-banner">
            <div className="edge-standby-beacon">
              <RadioTower size={24} />
            </div>
            <div className="edge-standby-info">
              <h3>No edge nodes currently connected.</h3>
              <p>Edge-node discovery is available and can be enabled through <code>ASTRAOS_EDGE_NODES</code>.</p>
            </div>
          </div>
          <div className="edge-standby-footer">
            <span>0 LIVE EDGE NODES</span>
          </div>
        </div>
      )}
      <div className="edge-capabilities-grid">
        <div className="edge-cap-item">
          <small>DISCOVERY</small>
          <b className={realNodes.length > 0 ? 'text-accent' : ''}>{realNodes.length > 0 ? 'CONNECTED' : 'READY'}</b>
        </div>
        <div className="edge-cap-item">
          <small>NODE REGISTRATION</small>
          <b className={realNodes.length > 0 ? 'text-accent' : ''}>{realNodes.length > 0 ? 'ACTIVE' : 'READY'}</b>
        </div>
        <div className="edge-cap-item">
          <small>REMOTE EXECUTION</small>
          <b>READY</b>
        </div>
        <div className="edge-cap-item">
          <small>TELEMETRY SYNC</small>
          <b className={realNodes.length > 0 ? 'text-accent' : ''}>{realNodes.length > 0 ? 'LIVE' : 'READY'}</b>
        </div>
      </div>
    </Panel>
  );
}

function SettingsPanel({ elite, id }) {
  const capabilityCount = elite.capabilities?.length || 0;
  const activeCapabilities = (elite.capabilities || []).filter((item) => item.active).length;
  const settings = [
    ['API Endpoint', API_BASE, 'FastAPI telemetry and control plane'],
    ['Telemetry Mode', elite.status || 'loading', 'Live WebSocket stream with REST fallback'],
    ['Host Adapters', `${activeCapabilities}/${capabilityCount} active`, 'Explicit hardware capability states'],
    ['Optimization Safety', 'Guarded actions', 'renice/taskset/cgroup adapters require host permission'],
    ['Proof Mode', '/proof/live', 'Raw JSON evidence, process IDs, and collector sources'],
    ['Architecture', '/architecture', 'Runtime topology and data flow']
  ];

  return (
    <Panel id={id} className="settings-panel" delay={0.46}>
      <PanelHeader icon={Settings} eyebrow="Settings" title="Runtime Configuration" action="local control plane" />
      <div className="settings-grid">
        {settings.map(([label, value, detail]) => (
          <div className="setting-card" key={label}>
            <small>{label}</small>
            <strong>{value}</strong>
            <span>{detail}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function DistributedFabricPanel({ distributed }) {
  const nodes = distributed?.nodes || [];
  return (
    <Panel className="fabric-panel" delay={0.31}>
      <PanelHeader icon={Network} eyebrow="Cluster Fabric" title="Multi-Node Infrastructure" action={distributed ? `health ${distributed.health_score}` : 'syncing'} />
      <div className="fabric-grid">
        {nodes.map((node) => (
          <div className="fabric-node" key={node.name}>
            <b>{node.name}</b>
            <small>{node.role}</small>
            <span>{node.workload}</span>
            <i>CPU {node.cpu_percent}%</i>
            <i>MEM {node.memory_percent}%</i>
            <i>NET {node.network_mbps} Mbps</i>
            <strong>{node.health_score}</strong>
          </div>
        ))}
      </div>
      <div className="orchestration-events">
        {(distributed?.orchestration_events || []).slice(0, 4).map((event, index) => (
          <p key={`${event.source}-${index}`}><span>{event.time}</span> {event.source} {'->'} {event.target}: {event.reason}</p>
        ))}
        {!distributed?.orchestration_events?.length && <p><span>sync</span> Cluster balanced. No workload migration required.</p>}
      </div>
    </Panel>
  );
}

function LiveLogStream({ events = [], id }) {
  return (
    <Panel id={id} className="log-stream-panel" delay={0.2}>
      <PanelHeader icon={Terminal} eyebrow="Live Infrastructure Logs" title="Operational Event Stream" action={`${events.length} events`} />
      <div className="live-log-stream">
        {(events.length ? events : [{ time: '--:--:--', node: 'astra-control-plane', message: 'Waiting for infrastructure events.', level: 'info' }]).slice(-14).map((event, index) => (
          <p key={`${event.timestamp}-${index}`} className={event.level || 'info'}>
            <span>[{event.time}]</span> <b>{event.node}</b> {event.message}
          </p>
        ))}
      </div>
    </Panel>
  );
}

function StressPanel() {
  const [status, setStatus] = useState('Ready');
  async function activate(mode) {
    setStatus(`Activating ${mode} chaos scenario...`);
    try {
      const response = await fetch(apiUrl(`/chaos/${mode}?intensity=1&duration_seconds=90`), { method: 'POST' });
      const payload = await response.json();
      setStatus(`${payload.mode} chaos active for distributed fabric`);
    } catch (error) {
      setStatus(`Chaos API error: ${error.message}`);
    }
  }
  return (
    <Panel className="stress-panel" delay={0.22}>
      <PanelHeader icon={Zap} eyebrow="Chaos Engineering Mode" title="Live Scenario Controls" action={status} />
      <div className="stress-buttons">
        {['cpu', 'memory', 'network', 'thermal', 'disk', 'node_crash', 'container_crash'].map((mode) => <button key={mode} type="button" onClick={() => activate(mode)}>{mode.replaceAll('_', ' ')}</button>)}
      </div>
    </Panel>
  );
}

function Benchmarks({ benchmarks, id }) {
  const metrics = (benchmarks.metrics || []).map((item) => ({
    name: item.name,
    before: Number(item.before),
    after: Number(item.after)
  })).filter((item) => Number.isFinite(item.before) && Number.isFinite(item.after));
  return (
    <Panel id={id} className="benchmark-panel" delay={0.35}>
      <PanelHeader icon={BarChart3} eyebrow="Panel 07" title="Performance Benchmarks" action={benchmarks.status || 'latest'} />
      {metrics.length ? (
        <>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={metrics}>
              <CartesianGrid stroke="rgba(132, 220, 255, 0.1)" vertical={false} />
              <XAxis dataKey="name" stroke="#7fa4b8" tickLine={false} axisLine={false} />
              <YAxis stroke="#7fa4b8" tickLine={false} axisLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="before" fill="#ff4f5e" radius={[5, 5, 0, 0]} />
              <Bar dataKey="after" fill="#00e7ff" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="benchmark-cards">
            {metrics.slice(0, 3).map((item) => <span key={item.name}>{item.name} <b>{item.before} {'->'} {item.after}</b></span>)}
          </div>
        </>
      ) : <EmptyState message={benchmarks.message || 'No real benchmark has been recorded yet.'} />}
    </Panel>
  );
}

function Timeline({ data }) {
  return (
    <Panel className="timeline-panel" delay={0.4}>
      <PanelHeader icon={Activity} eyebrow="Bottom Section" title="Performance Timeline" action="Real telemetry window" />
      {data.length ? (
        <ResponsiveContainer width="100%" height={170}>
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(132, 220, 255, 0.1)" vertical={false} />
            <XAxis dataKey="time" stroke="#7fa4b8" tickLine={false} axisLine={false} />
            <YAxis stroke="#7fa4b8" tickLine={false} axisLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Line type="monotone" dataKey="cpu" stroke="#00e7ff" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="memory" stroke="#b967ff" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="net" stroke="#7cffb2" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="disk" stroke="#ff4f9a" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : <EmptyState message="Waiting for real telemetry history." />}
    </Panel>
  );
}

function EliteRuntime({ elite }) {
  const cards = [
    ['Workload', elite.workload?.category || elite.status, elite.workload?.confidence ? `confidence ${elite.workload.confidence}` : 'live classifier'],
    ['Self-Healing', `${elite.healing?.incidents?.length ?? 0} incidents`, elite.healing?.recovery_plan?.[0]?.action || 'no mitigation needed'],
    ['Security', elite.security?.risk_level || 'unknown', `risk score ${elite.security?.risk_score ?? 'n/a'}`],
    ['Kernel Observability', elite.kernel_observability?.available ? 'active' : 'adapter inactive', elite.kernel_observability?.bpftrace || elite.kernel_observability?.perf || 'requires Linux perf/eBPF tooling'],
    ['Containers', elite.containers?.containerized ? 'detected' : 'runtime ready', elite.containers?.docker?.available ? 'docker adapter available' : 'docker CLI not reporting workloads'],
    ['Digital Twin', elite.digital_twin?.recommended_strategy || 'warming', `${elite.digital_twin?.states?.length ?? 0} future states`],
    ['Scheduler Delta', elite.scheduler_simulation?.improvement_estimate?.latency_score_delta ?? 'n/a', 'Astra vs CFS model'],
    ['Model Versions', `${elite.models?.length ?? 0}`, 'trained artifacts']
  ];
  return (
    <Panel className="elite-panel" delay={0.42}>
      <PanelHeader icon={BrainCircuit} eyebrow="Elite Runtime" title="Autonomous Infrastructure Intelligence" action={elite.status || 'loading'} />
      <div className="elite-grid">
        {cards.map(([label, value, detail]) => (
          <div className="elite-card" key={label}>
            <small>{label}</small>
            <strong>{value}</strong>
            <span>{detail}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function PredictiveNotificationCenter({ alertState }) {
  const alerts = alertState?.alerts || [];
  const [permission, setPermission] = useState(typeof Notification !== 'undefined' ? Notification.permission : 'unsupported');
  async function enableNotifications() {
    if (typeof Notification === 'undefined') return;
    const result = await Notification.requestPermission();
    setPermission(result);
  }
  return (
    <Panel className="notification-panel" delay={0.41}>
      <PanelHeader
        icon={ShieldCheck}
        eyebrow="Predictive Notification Center"
        title="Future Failure Alerts"
        action={`${alerts.length} active / ${permission}`}
      />
      {permission !== 'granted' && permission !== 'unsupported' && (
        <div className="notification-enable">
          <button type="button" onClick={enableNotifications}>Enable Desktop Alerts</button>
        </div>
      )}
      <div className="notification-list">
        {(alerts.length ? alerts : [{ alert_id: 'stable', risk_level: 'info', category: 'INFO', title: 'No predictive incidents active', message: 'AstraOS is monitoring trends and will alert before resource failure.', confidence_score: 0.82 }]).slice(0, 5).map((alert) => (
          <div className={`notification-card ${alert.risk_level}`} key={alert.alert_id}>
            <small>{alert.category || 'INFO'} / confidence {Math.round(Number(alert.confidence_score || 0) * 100)}%</small>
            <b>{alert.title}</b>
            <span>{alert.message}</span>
            <span>Current {alert.current_value ?? 'n/a'} / predicted {alert.predicted_value ?? 'n/a'} / risk score {alert.risk_score ?? 'n/a'}</span>
            {alert.expected_failure_label && <span>Predicted failure time: {alert.expected_failure_label}</span>}
            {(alert.why || []).slice(0, 2).map((reason) => <em key={reason}>{reason}</em>)}
            {alert.time_remaining_minutes && <i>{alert.time_remaining_minutes} min remaining / expected {alert.expected_failure_label}</i>}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function PredictionTimelinePanel({ alertState }) {
  const timeline = alertState?.timeline || [];
  return (
    <Panel className="prediction-timeline-panel" delay={0.42}>
      <PanelHeader icon={Activity} eyebrow="Prediction Timeline" title="Now To Predicted Event" action={alertState?.reliability_index ? `${alertState.reliability_index.score}/100 reliability` : 'warming'} />
      <div className="prediction-line">
        {(timeline.length ? timeline : [{ label: 'NOW', value: 0, risk_level: 'info', resource: 'runtime', confidence: 0.7 }]).map((item, index) => (
          <div className={`prediction-step ${item.risk_level}`} key={`${item.label}-${index}`}>
            <small>{item.label}</small>
            <b>{item.resource}: {item.value}</b>
            <span>{item.trend || 'stable'} / {Math.round(Number(item.confidence || 0) * 100)}%</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ReliabilityPanel({ alertState }) {
  const reliability = alertState?.reliability_index || { score: 0, trend: 'warming' };
  const summary = alertState?.executive_summary || 'AstraOS is collecting telemetry for the executive summary.';
  const prevention = alertState?.prevention_counter || { downtime_prevented_label: '0h 0m', incidents_avoided: 0, optimization_savings_percent: 0 };
  return (
    <Panel className="reliability-panel" delay={0.43}>
      <PanelHeader icon={Gauge} eyebrow="AstraOS Reliability Index" title="Predictive Operations Score" action={reliability.trend} />
      <div className="reliability-body">
        <strong>{reliability.score}</strong>
        <span>{summary}</span>
      </div>
      <div className="prevention-grid">
        <span>Downtime Prevented <b>{prevention.downtime_prevented_label}</b></span>
        <span>Incidents Avoided <b>{prevention.incidents_avoided}</b></span>
        <span>Optimization Savings <b>{prevention.optimization_savings_percent}%</b></span>
      </div>
    </Panel>
  );
}

function RecruiterDemoPanel({ alertState }) {
  const flow = alertState?.demo_flow || [
    { stage: 'Observe', status: 'Telemetry warming', detail: 'Start the API to stream host metrics.' },
    { stage: 'Predict', status: 'Waiting for model window', detail: 'AstraOS will forecast future failures.' },
    { stage: 'Decide', status: 'Explainability pending', detail: 'Root-cause engine is collecting samples.' },
    { stage: 'Act', status: 'Guarded optimization ready', detail: 'Apply mode remains protected.' },
    { stage: 'Verify', status: 'Proof pending', detail: 'Before/after evidence appears after action.' }
  ];
  return (
    <Panel className="demo-flow-panel" delay={0.44}>
      <PanelHeader icon={Sparkles} eyebrow="Recruiter Demo Mode" title="Observe -> Predict -> Decide -> Act -> Verify" action="one-click story" />
      <div className="demo-flow-grid">
        {flow.map((step) => (
          <div className="demo-step" key={step.stage}>
            <small>{step.stage}</small>
            <b>{step.status}</b>
            <span>{step.detail}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function PredictiveToastLayer({ alertState }) {
  const alerts = alertState?.alerts || [];
  const [dismissed, setDismissed] = useState({});
  const visibleAlerts = alerts.filter((alert) => !dismissed[alert.alert_id]).slice(0, 3);
  if (!visibleAlerts.length) return null;
  return (
    <div className="predictive-toast-layer" aria-live="polite">
      {visibleAlerts.map((alert) => (
        <motion.div
          className={`predictive-toast ${alert.risk_level || 'info'}`}
          key={alert.alert_id}
          initial={{ opacity: 0, x: 28, scale: 0.98 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          transition={{ duration: 0.25 }}
        >
          <button type="button" aria-label="Dismiss alert" onClick={() => setDismissed((current) => ({ ...current, [alert.alert_id]: true }))}>x</button>
          <small>{formatRiskName(alert.risk_level)} / {Math.round(Number(alert.confidence_score || 0) * 100)}% confidence</small>
          <b>{formatRiskTitle(alert)}</b>
          <span>{alert.message}</span>
          {alert.time_remaining_minutes && <i>Expected in about {alert.time_remaining_minutes} min.</i>}
          {(alert.recommended_actions || []).slice(0, 1).map((rec) => (
            <em key={rec.action}>{rec.action} | Benefit: {rec.expected_benefit}</em>
          ))}
        </motion.div>
      ))}
    </div>
  );
}

function UserRiskNotificationsPanel({ alertState }) {
  const alerts = alertState?.alerts || [];
  const [permission, setPermission] = useState(typeof Notification === 'undefined' ? 'unsupported' : Notification.permission);
  function enableNotifications() {
    if (typeof Notification === 'undefined') {
      setPermission('unsupported');
      return;
    }
    Notification.requestPermission().then((nextPermission) => {
      setPermission(nextPermission);
      if (nextPermission === 'granted') {
        new Notification('AstraOS risk alerts enabled', {
          body: 'AstraOS will notify you before predicted CPU, memory, thermal, disk, or network risk becomes critical.',
          tag: 'astraos-risk-alerts-enabled'
        });
      }
    });
  }
  const visibleAlerts = alerts.length ? alerts : [{
    alert_id: 'healthy-runtime',
    risk_level: 'info',
    affected_resource: 'system',
    confidence_score: 0.82,
    title: 'System is currently stable',
    message: 'AstraOS is watching live trends and will notify before predicted resource pressure becomes critical.',
    recommended_actions: []
  }];
  return (
    <Panel className="user-risk-panel" delay={0.415}>
      <PanelHeader icon={ShieldCheck} eyebrow="User Notifications" title="Predictive Risk Warnings" action={permission === 'granted' ? 'browser enabled' : 'dashboard active'} />
      <div className="risk-permission-bar">
        <span>{permission === 'granted' ? 'Browser notifications are enabled.' : permission === 'denied' ? 'Browser notifications are blocked in this browser.' : permission === 'unsupported' ? 'This browser does not support notifications.' : 'Enable desktop alerts so AstraOS can warn you before risk occurs.'}</span>
        {permission === 'default' && <button type="button" onClick={enableNotifications}>Enable</button>}
      </div>
      <div className="risk-alert-list">
        {visibleAlerts.slice(0, 4).map((alert) => (
          <div className={`risk-alert-card ${alert.risk_level || 'info'}`} key={alert.alert_id}>
            <small>{formatRiskName(alert.risk_level)} / {Math.round(Number(alert.confidence_score || 0) * 100)}% confidence</small>
            <b>{formatRiskTitle(alert)}</b>
            <span>{alert.message}</span>
            {alert.time_remaining_minutes && <i>Expected before failure: about {alert.time_remaining_minutes} minutes.</i>}
            {(alert.recommended_actions || []).slice(0, 2).map((rec) => (
              <em key={rec.action}>{rec.action} | Benefit: {rec.expected_benefit} | Risk: {rec.risk}</em>
            ))}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function formatRiskName(risk) {
  if (risk === 'critical') return 'Critical risk';
  if (risk === 'warning') return 'Warning';
  if (risk === 'predictive') return 'Predictive watch';
  return 'Healthy';
}

function formatRiskTitle(alert) {
  const resource = String(alert?.affected_resource || 'system').replaceAll('_', ' ');
  if (alert?.time_remaining_minutes) return `${resource.toUpperCase()} pressure predicted before it happens`;
  return alert?.title || `${resource.toUpperCase()} is stable`;
}

function OptimizationProofPanel({ proof }) {
  const metrics = proof?.metrics || [];
  return (
    <Panel className="proof-panel" delay={0.43}>
      <PanelHeader icon={Gauge} eyebrow="Before vs After Proof" title="Optimization Effectiveness" action={proof?.status || 'waiting'} />
      <div className="proof-score">
        <strong>{proof?.effectiveness_score ?? '--'}</strong>
        <span>{proof?.summary || 'Waiting for a measured optimization apply run or benchmark artifact.'}</span>
      </div>
      <div className="proof-metrics">
        {metrics.slice(0, 6).map((metric) => (
          <div className={metric.direction === 'improved' ? 'proof-metric improved' : 'proof-metric'} key={metric.name}>
            <small>{metric.name}</small>
            <b>{metric.before} {'->'} {metric.after} {metric.unit}</b>
            <span>{metric.improvement_percent ? `${metric.improvement_percent}%` : metric.direction || 'recorded'}</span>
          </div>
        ))}
        {!metrics.length && <EmptyState message="Run a benchmark or apply a guarded optimization to populate before/after proof." />}
      </div>
    </Panel>
  );
}

function RootCausePanel({ rootCause }) {
  const findings = rootCause?.findings || [];
  return (
    <Panel className="root-cause-panel" delay={0.45}>
      <PanelHeader icon={BrainCircuit} eyebrow="AI Root Cause Analysis" title="Explainable Runtime Intelligence" action={rootCause?.status || 'warming'} />
      <p className="rca-summary">{rootCause?.summary || 'Root-cause engine is waiting for live telemetry.'}</p>
      <div className="rca-findings">
        {findings.slice(0, 3).map((finding) => (
          <div className={`rca-finding ${finding.severity || 'info'}`} key={finding.type}>
            <b>{finding.type?.replaceAll('_', ' ')}</b>
            <small>confidence {Math.round(Number(finding.confidence || 0) * 100)}%</small>
            {(finding.reasoning || []).slice(0, 3).map((reason) => <span key={reason}>{reason}</span>)}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function IncidentTimelinePanel({ incident }) {
  const timeline = incident?.timeline || [];
  return (
    <Panel className="incident-panel" delay={0.47}>
      <PanelHeader icon={Activity} eyebrow="Incident Timeline" title="Detection -> Recovery Flow" action={incident?.incident_id || 'observe'} />
      <div className="incident-strip">
        {timeline.slice(-8).map((item, index) => (
          <div className={`incident-step ${item.severity || 'info'}`} key={`${item.timestamp}-${index}`}>
            <small>{item.time} / {item.phase}</small>
            <b>{item.node}</b>
            <span>{item.message}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function PipelineDebugPanel({ debug = [] }) {
  return (
    <Panel className="pipeline-debug-panel" delay={0.32}>
      <PanelHeader icon={Terminal} eyebrow="Pipeline Debug" title="Telemetry -> Prediction -> Alert -> Dashboard" action={`${debug.length} checkpoints`} />
      <div className="pipeline-debug-list">
        {(debug.length ? debug : [{ time: '--:--:--', stage: 'warming', message: 'Waiting for pipeline checkpoints.', metrics: {} }]).slice(-10).map((item, index) => (
          <div className="pipeline-debug-item" key={`${item.timestamp || index}-${item.stage}`}>
            <small>{item.time} / {item.stage}</small>
            <b>{item.message}</b>
            <span>{Object.entries(item.metrics || {}).map(([key, value]) => `${key}: ${value}`).join(' | ') || 'No metric payload'}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function CapabilityMatrix({ capabilities = [] }) {
  return (
    <Panel className="capability-panel" delay={0.44}>
      <PanelHeader icon={ShieldCheck} eyebrow="Capability Matrix" title="Host Adapter State" action="explicit states" />
      <div className="capability-grid">
        {capabilities.map((item) => (
          <div className={item.active ? 'capability active' : 'capability inactive'} key={item.name}>
            <b>{item.name}</b>
            <span>{item.message}</span>
            {item.remediation && <small>{item.remediation}</small>}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ProofPage() {
  const proof = useProof();
  return (
    <div className="astra-app proof-mode">
      <div className="particle-field" />
      <div className="grid-overlay" />
      <main className="proof-main">
        <Logo />
        <h1>Proof Mode</h1>
        <p>Raw runtime evidence from AstraOS collectors, process IDs, WebSocket-equivalent payloads, benchmark artifacts, optimization plans, and source adapter states.</p>
        <pre>{JSON.stringify(proof, null, 2)}</pre>
      </main>
    </div>
  );
}

function ArchitecturePage() {
  const architecture = useArchitecture();
  return (
    <div className="astra-app proof-mode">
      <div className="particle-field" />
      <div className="grid-overlay" />
      <main className="proof-main architecture-main">
        <Logo />
        <h1>Architecture</h1>
        <p>Telemetry collectors, AI engine, optimization layer, distributed nodes, storage pipeline, WebSocket streams, and observability flow.</p>
        <div className="architecture-diagram">
          {(architecture.layers || []).map((layer) => (
            <div className="architecture-layer" key={layer.id}>
              <b>{layer.label}</b>
              {(layer.items || []).map((item) => <span key={item}>{item}</span>)}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <b>{label}</b>
      {payload.map((item) => (
        <span key={item.dataKey} style={{ color: item.color }}>{item.dataKey}: {item.value}</span>
      ))}
    </div>
  );
}

function App() {
  const path = window.location.pathname;
  if (path.startsWith('/proof')) return <ProofPage />;
  if (path.startsWith('/architecture')) return <ArchitecturePage />;
  const clock = useClock();
  const telemetry = useLiveTelemetry();
  const benchmarks = useBenchmarks();
  const elite = useEliteStatus();
  const [activeSection, setActiveSection] = useState('dashboard-overview');
  const chartData = useMemo(() => (telemetry.history || []).map(chartPoint), [telemetry.history]);
  const alertState = telemetry.predictiveAlerts || elite.predictive_alerts;
  useBrowserPredictiveNotifications(alertState);

  function navigateToSection(sectionId) {
    setActiveSection(sectionId);
    const target = document.getElementById(sectionId);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
    }
  }

  return (
    <div className="astra-app">
      <div className="particle-field" />
      <div className="grid-overlay" />
      <TopNav clock={clock} telemetry={telemetry} />
      <Sidebar activeSection={activeSection} onNavigate={navigateToSection} />
      <main className="command-grid">
        <OverviewHero id="dashboard-overview" latest={telemetry.latest} prediction={telemetry.prediction} />
        <CPUIntelligence id="cpu-intelligence" data={chartData} latest={telemetry.latest} prediction={telemetry.prediction} />
        <ThermalEngine id="thermal-engine" data={chartData} latest={telemetry.latest} prediction={telemetry.prediction} />
        <MemoryEngine id="memory-optimizer" latest={telemetry.latest} prediction={telemetry.prediction} />
        <PowerOptimization data={chartData} latest={telemetry.latest} prediction={telemetry.prediction} />
        <EdgeExecution id="distributed-edge" nodes={telemetry.nodes} />
        <DistributedFabricPanel distributed={telemetry.distributed || elite.distributed} />
        <StressPanel />
        <ProcessMonitorPanel id="process-monitor" latest={telemetry.latest} />
        <Benchmarks id="benchmarks" benchmarks={benchmarks} />
        <EliteRuntime elite={elite} />
        <PredictiveNotificationCenter alertState={alertState} />
        <PredictionTimelinePanel alertState={alertState} />
        <ReliabilityPanel alertState={alertState} />
        <RecruiterDemoPanel alertState={alertState} />
        <OptimizationProofPanel proof={elite.optimization_proof} />
        <RootCausePanel rootCause={elite.root_cause} />
        <IncidentTimelinePanel incident={telemetry.incidentTimeline || elite.incident_timeline} />
        <CapabilityMatrix capabilities={elite.capabilities || []} />
        <Timeline data={chartData} />
        <SettingsPanel id="settings" elite={elite} />
      </main>
      <aside className="ai-rail">
        <DecisionPanel id="ai-predictions" prediction={telemetry.prediction} telemetry={telemetry} />
        <LiveLogStream id="logs" events={telemetry.events || elite.events || []} />
        <PipelineDebugPanel debug={telemetry.pipelineDebug || []} />
        <AssistantPanel prediction={telemetry.prediction} alertState={alertState} />
        <Recommendations latest={telemetry.latest} prediction={telemetry.prediction} />
        <PredictiveToastLayer alertState={alertState} />
      </aside>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);

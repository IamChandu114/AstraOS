'use client'
import { useCallback, useEffect, useState } from 'react'
import { Activity, AlertTriangle, BrainCircuit, Circle, RefreshCw } from 'lucide-react'
import { ArrowLink, SectionLabel, Shell, Status } from '@/components/astraos'
import { extractMetrics, fetchRuntime, metricValue, runtimeWebSocket, type RuntimeConnection } from '@/lib/runtime'

const panels: [string, string][] = [
  ['CPU', 'cpu'],
  ['MEMORY', 'memory'],
  ['PROCESSES', 'processes'],
  ['DISK', 'disk'],
  ['NETWORK', 'network'],
  ['THERMAL', 'thermal'],
]

export default function RuntimePage() {
  const [state, setState] = useState<RuntimeConnection>('CONNECTING')
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null)
  const [attempt, setAttempt] = useState(0)

  const connect = useCallback(() => {
    let active = true
    setState('CONNECTING')
    const controller = new AbortController()

    fetchRuntime('/metrics', controller.signal)
      .then(data => { if (active) { setMetrics(extractMetrics(data)); setState('LIVE') } })
      .catch(() => { if (active) { setMetrics(null); setState('OFFLINE') } })

    const socket = runtimeWebSocket('/ws/telemetry')
    if (socket) {
      socket.onopen = () => active && setState('LIVE')
      socket.onmessage = e => { try { setMetrics(extractMetrics(JSON.parse(e.data))) } catch {} }
      socket.onerror = () => active && setState('DEGRADED')
      socket.onclose = () => active && setState('OFFLINE')
    }

    return () => { active = false; controller.abort(); socket?.close() }
  }, [attempt])

  useEffect(() => connect(), [connect])

  const dashboardUrl = process.env.NEXT_PUBLIC_ASTRAOS_DASHBOARD_URL

  return (
    <Shell>
      <section className="border-b hairline">
        <div className="mx-auto max-w-7xl px-5 pb-14 pt-16 lg:px-8 lg:pb-20 lg:pt-24">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div>
              <SectionLabel number="RUNTIME / 00">LIVE SYSTEM SURFACE</SectionLabel>
              <h1 className="mt-6 text-5xl font-medium tracking-[-.055em] md:text-6xl">Runtime command center.</h1>
              <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground">
                A direct view into the AstraOS service layer. Live telemetry is never simulated; unavailable fields remain unavailable.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <Status label="ONLINE" tone="accent" />
              {dashboardUrl ? (
                <a href={dashboardUrl} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-2 border border-accent px-3 py-2 mono text-[10px] tracking-[.1em] text-accent transition-colors hover:bg-accent hover:text-background"
                  aria-label="Experience live AstraOS dashboard">
                  <span className="size-1.5 rounded-full bg-accent" aria-hidden="true" /> EXPERIENCE LIVE ASTRAOS
                </a>
              ) : (
                <button type="button" disabled
                  className="inline-flex cursor-not-allowed items-center gap-2 border hairline px-3 py-2 mono text-[10px] tracking-[.1em] text-muted-foreground"
                  aria-label="Live AstraOS dashboard unavailable">
                  <span className="size-1.5 rounded-full bg-muted-foreground" aria-hidden="true" /> LIVE ASTRAOS UNAVAILABLE
                </button>
              )}
              <button onClick={() => setAttempt(a => a + 1)}
                className="inline-flex items-center gap-2 border hairline px-3 py-2 mono text-[10px] tracking-[.1em] hover:border-accent"
                aria-label="Retry runtime connection">
                <RefreshCw className="size-3" /> RETRY
              </button>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8 lg:py-16">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {panels.map(([label, key]) => (
            <div key={key} className="border hairline bg-card p-5">
              <div className="flex justify-between">
                <span className="mono text-[10px] text-muted-foreground">{label}</span>
                <Activity className="size-4 text-muted-foreground" />
              </div>
              <div className="mt-10 mono text-2xl text-foreground">{metricValue(metrics, key)}</div>
              <div className="mt-2 mono text-[10px] text-muted-foreground">
                {metrics ? 'RUNTIME VALUE' : 'WAITING FOR RUNTIME'}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 grid gap-3 lg:grid-cols-[1.2fr_.8fr]">
          <div className="border hairline bg-card p-6">
            <div className="flex items-center gap-3">
              <BrainCircuit className="size-5 text-accent" />
              <SectionLabel>AI DECISION PIPELINE</SectionLabel>
            </div>
            <div className="mt-8 grid grid-cols-2 gap-2 sm:grid-cols-3">
              {['COLLECT', 'CLASSIFY', 'FORECAST', 'DETECT', 'PLAN', 'VERIFY'].map((x, i) => (
                <div key={x} className="border hairline p-4">
                  <span className="mono text-[10px] text-muted-foreground">0{i + 1}</span>
                  <div className="mt-5 text-xs">{x}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="border hairline bg-card p-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="size-4 text-muted-foreground" />
              <SectionLabel>EVENT TIMELINE</SectionLabel>
            </div>
            <div className="mt-8 space-y-4 mono text-[10px] text-muted-foreground">
              <div className="flex gap-3">
                <Circle className="mt-0.5 size-2 fill-current" />
                {metrics ? 'Telemetry frame received' : 'Waiting for event stream'}
              </div>
              <div className="flex gap-3"><Circle className="mt-0.5 size-2" /> Root-cause analysis unavailable</div>
              <div className="flex gap-3"><Circle className="mt-0.5 size-2" /> Optimization proof unavailable</div>
            </div>
          </div>
        </div>

        <div className="mt-10">
          <ArrowLink href="/documentation">Read runtime documentation</ArrowLink>
        </div>
      </div>
    </Shell>
  )
}


export type RuntimeConnection = 'LIVE' | 'CONNECTING' | 'OFFLINE' | 'DEGRADED'

/** Derive WebSocket base from HTTP API base when not explicitly provided.
 *  http://host:port → ws://host:port
 *  https://host:port → wss://host:port
 */
function deriveWsBase(apiBase: string, explicit: string): string {
  if (explicit) return explicit
  if (!apiBase) return ''
  return apiBase.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
}

const _apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.VITE_API_BASE_URL || ''
const _wsExplicit = process.env.NEXT_PUBLIC_WS_BASE_URL || process.env.VITE_WS_BASE_URL || ''

export const runtimeConfig = {
  apiBase: _apiBase,
  wsBase: deriveWsBase(_apiBase, _wsExplicit),
}

export async function fetchRuntime(path: string, signal?: AbortSignal) {
  if (!runtimeConfig.apiBase) throw new Error('Runtime endpoint is not configured')
  const response = await fetch(`${runtimeConfig.apiBase.replace(/\/$/, '')}${path}`, { signal, headers: { Accept: 'application/json' }, cache: 'no-store' })
  if (!response.ok) throw new Error(`Runtime responded with ${response.status}`)
  return response.json() as Promise<Record<string, unknown>>
}

export function runtimeWebSocket(path: string) {
  if (typeof window === 'undefined' || !runtimeConfig.wsBase) return null
  return new WebSocket(`${runtimeConfig.wsBase.replace(/\/$/, '')}${path}`)
}

/**
 * Extract the metric payload from a raw API response.
 * FastAPI /metrics returns: { status, latest: { cpu, memory, ... }, history: [...] }
 * WebSocket frames may send the same shape or just the latest object directly.
 */
export function extractMetrics(raw: Record<string, unknown>): Record<string, unknown> | null {
  if (!raw) return null
  // Standard shape: { status, latest: {...} }
  if (raw.latest && typeof raw.latest === 'object') return raw.latest as Record<string, unknown>
  // Flat shape (direct send or legacy)
  return raw
}

/**
 * Extract a display value from a nested metric key.
 * e.g. key="cpu" → raw.usage_percent; key="memory" → raw.percent
 */
export function metricValue(metrics: Record<string, unknown> | null, key: string): string {
  if (!metrics) return '—'
  const section = metrics[key]
  if (section == null) return '—'
  if (typeof section === 'number') return section.toFixed(1)
  if (typeof section === 'object') {
    const s = section as Record<string, unknown>
    // known sub-keys per FastAPI backend schema
    const candidates: Record<string, string> = {
      cpu: 'usage_percent',
      memory: 'percent',
      disk: 'usage_percent',
      thermal: 'hottest_c',
      network: 'bytes_recv_per_sec',
      processes: 'total',
    }
    const subKey = candidates[key]
    const val = subKey ? s[subKey] : Object.values(s)[0]
    if (val == null) return '—'
    if (typeof val === 'number') {
      if (key === 'network') return `${(val / 1024).toFixed(1)} KB/s`
      if (key === 'thermal') return `${val.toFixed(1)} °C`
      if (key === 'processes') return String(Math.round(val as number))
      return `${(val as number).toFixed(1)}%`
    }
    return String(val)
  }
  return String(section)
}


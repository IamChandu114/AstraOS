export type RuntimeConnection = 'LIVE' | 'CONNECTING' | 'OFFLINE' | 'DEGRADED'

export const runtimeConfig = {
  apiBase: process.env.NEXT_PUBLIC_API_BASE_URL || process.env.VITE_API_BASE_URL || '',
  wsBase: process.env.NEXT_PUBLIC_WS_BASE_URL || process.env.VITE_WS_BASE_URL || '',
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

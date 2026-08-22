'use client'

import { useEffect, useState } from 'react'
import { Circle } from 'lucide-react'
import { runtimeConfig, type RuntimeConnection } from '@/lib/runtime'

const POLL_INTERVAL_MS = 15_000
const TIMEOUT_MS = 5_000

async function checkHealth(signal: AbortSignal): Promise<boolean> {
  try {
    const base = runtimeConfig.apiBase
    if (!base) return false
    const res = await fetch(`${base.replace(/\/$/, '')}/health`, {
      signal,
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) return false
    const json = await res.json()
    return json?.status === 'ok'
  } catch {
    return false
  }
}

export function RuntimeStatus() {
  const [state, setState] = useState<RuntimeConnection>(
    runtimeConfig.apiBase ? 'CONNECTING' : 'OFFLINE'
  )

  useEffect(() => {
    if (!runtimeConfig.apiBase) {
      setState('OFFLINE')
      return
    }

    let active = true

    async function poll() {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
      const online = await checkHealth(controller.signal)
      clearTimeout(timer)
      if (active) setState(online ? 'LIVE' : 'OFFLINE')
    }

    // Immediate first check
    poll()

    // Periodic re-check
    const interval = setInterval(poll, POLL_INTERVAL_MS)

    return () => {
      active = false
      clearInterval(interval)
    }
  }, [])

  const label =
    state === 'LIVE' ? 'ONLINE' :
    state === 'CONNECTING' ? 'CONNECTING' :
    state === 'DEGRADED' ? 'DEGRADED' :
    'OFFLINE'

  return (
    <span
      role="status"
      className={`mono inline-flex items-center gap-2 text-[10px] tracking-[.1em] ${
        state === 'LIVE' ? 'text-accent' :
        state === 'DEGRADED' ? 'text-amber-300' :
        'text-muted-foreground'
      }`}
      aria-label={`Runtime status: ${label}`}
    >
      <Circle className="size-2 fill-current" />
      RUNTIME-{label}
    </span>
  )
}

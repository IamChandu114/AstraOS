'use client'

import { useEffect, useState } from 'react'
import { Circle } from 'lucide-react'
import { fetchRuntime, runtimeConfig, type RuntimeConnection } from '@/lib/runtime'

export function RuntimeStatus() {
  const [state, setState] = useState<RuntimeConnection>(runtimeConfig.apiBase ? 'CONNECTING' : 'OFFLINE')

  useEffect(() => {
    if (!runtimeConfig.apiBase) return
    const controller = new AbortController()
    fetchRuntime('/health', controller.signal)
      .then(() => setState('LIVE'))
      .catch(() => setState('OFFLINE'))
    return () => controller.abort()
  }, [])

  const label = state === 'LIVE' ? 'LIVE' : state === 'CONNECTING' ? 'CONNECTING' : state === 'DEGRADED' ? 'DEGRADED' : 'OFFLINE'
  return <span role="status" className={`mono inline-flex items-center gap-2 text-[10px] tracking-[.1em] ${state === 'LIVE' ? 'text-accent' : state === 'DEGRADED' ? 'text-amber-300' : 'text-muted-foreground'}`} aria-label={`Runtime status: ${label}`}><Circle className="size-2 fill-current" />RUNTIME-{label}</span>
}

'use client'

import { useEffect, useState } from 'react'
import { Circle } from 'lucide-react'
import { runtimeConfig } from '@/lib/runtime'

type StatusItem = { label: string; value: string; tone?: 'accent' | 'muted' }

export function SystemStatus() {
  const [runtime, setRuntime] = useState('OFFLINE')
  useEffect(() => {
    if (!runtimeConfig.apiBase) return
    const controller = new AbortController()
    fetch(`${runtimeConfig.apiBase}/health`, { signal: controller.signal })
      .then((response) => setRuntime(response.ok ? 'LIVE' : 'DEGRADED'))
      .catch(() => setRuntime('OFFLINE'))
    return () => controller.abort()
  }, [])
  const items: StatusItem[] = [
    { label: 'RUNTIME', value: runtime, tone: runtime === 'LIVE' ? 'accent' : 'muted' },
    { label: 'TELEMETRY', value: runtime === 'LIVE' ? 'BOUND' : 'UNBOUND', tone: runtime === 'LIVE' ? 'accent' : 'muted' },
    { label: 'AI ENGINE', value: runtime === 'LIVE' ? 'AVAILABLE' : 'UNAVAILABLE' },
    { label: 'WEBSOCKET', value: runtime === 'LIVE' ? 'CONFIGURED' : 'DISCONNECTED' },
    { label: 'BENCHMARKS', value: 'NOT AVAILABLE' },
    { label: 'EVIDENCE', value: 'ILLUSTRATIVE' },
  ]
  return <section aria-label="System status" className="border-b hairline bg-card"><div className="mx-auto grid max-w-7xl divide-y hairline px-5 sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-6 lg:px-8">{items.map((item) => <div key={item.label} className="flex items-center justify-between gap-4 px-0 py-4 sm:px-4 lg:block lg:px-4"><div className="mono text-[9px] tracking-[.12em] text-muted-foreground">{item.label}</div><div className={`mt-1 flex items-center gap-2 mono text-[10px] tracking-[.08em] ${item.tone === 'accent' ? 'text-accent' : 'text-muted-foreground'}`}><Circle className="size-1.5 fill-current" />{item.value}</div></div>)}</div></section>
}
    

'use client'

import { useRef, useState } from 'react'
import { FileText, Play, X } from 'lucide-react'
import { ArrowLink, SectionLabel } from '@/components/astraos'

const index = [
  ['01', 'Problem', 'Why infrastructure telemetry alone is insufficient'],
  ['02', 'Architecture', 'The AstraOS runtime and intelligence stack'],
  ['03', 'Telemetry', 'System-level observation and data collection'],
  ['04', 'AI Intelligence', 'Workload classification and forecasting'],
  ['05', 'Policy', 'Prediction → decision → constrained action'],
  ['06', 'Runtime', 'Live system intelligence and observability'],
  ['07', 'Evidence', 'Benchmarks, experiments, and limitations'],
  ['08', 'Future Work', 'Kernel control, distributed edge intelligence, and research direction'],
]

export function Presentation({ source = process.env.NEXT_PUBLIC_ASTRAOS_PRESENTATION_URL }: { source?: string }) {
  const video = useRef<HTMLVideoElement>(null)
  const [transcript, setTranscript] = useState(false)
  const hasVideo = Boolean(source)

  return <section id="presentation" className="border-y hairline bg-card" aria-labelledby="presentation-title">
    <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-24">
      <div className="grid gap-12 lg:grid-cols-[1.1fr_.9fr] lg:items-end">
        <div>
          <SectionLabel number="03">ASTRAOS / PROJECT PRESENTATION</SectionLabel>
          <h2 id="presentation-title" className="mt-5 max-w-2xl text-4xl font-medium leading-[1.05] tracking-[-.05em] md:text-5xl">See AstraOS in operation.</h2>
          <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground">A technical walkthrough of the AstraOS architecture, intelligence pipeline, runtime behavior, observability stack, and optimization workflow.</p>
        </div>
        <p className="mono text-[10px] leading-5 tracking-[.08em] text-muted-foreground lg:text-right">ENGINEERING ARTIFACT / NOT A PROMOTIONAL DEMO<br />PRESENTATION INDEX FOLLOWS THE SYSTEM PATH</p>
      </div>

      <div className="mt-12 overflow-hidden border hairline bg-background">
        <div className="relative aspect-video">
          {hasVideo ? <video ref={video} src={source} className="size-full bg-black object-contain" controls playsInline preload="metadata" aria-label="AstraOS technical project presentation"><track kind="captions" src={process.env.NEXT_PUBLIC_ASTRAOS_PRESENTATION_CAPTIONS_URL} srcLang="en" label="English captions" default={Boolean(process.env.NEXT_PUBLIC_ASTRAOS_PRESENTATION_CAPTIONS_URL)} /></video> : <div className="grid size-full place-items-center p-8 text-center"><div><div className="mx-auto mb-6 flex size-14 items-center justify-center border border-accent text-accent"><Play className="size-5" /></div><div className="mono text-xs tracking-[.16em] text-accent">ASTRAOS</div><div className="mt-2 text-xl font-medium tracking-[-.03em]">TECHNICAL PRESENTATION</div><p className="mt-4 text-sm text-muted-foreground">Project presentation video will appear here.</p><div className="mt-6 mono text-[10px] tracking-[.1em] text-muted-foreground">VIDEO NOT ATTACHED</div></div></div>}
        </div>
        <div className="grid border-t hairline sm:grid-cols-4">
          <Meta label="PRESENTATION" value="AstraOS Technical Walkthrough" />
          {source && <Meta label="STATUS" value="PRESENTATION / AVAILABLE" accent />}
          {process.env.NEXT_PUBLIC_ASTRAOS_VERSION && <Meta label="VERSION" value={process.env.NEXT_PUBLIC_ASTRAOS_VERSION} />}
          {source && <Meta label="SOURCE" value="Configured media" />}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-5">
        <button type="button" onClick={() => setTranscript(!transcript)} className="inline-flex items-center gap-2 border-b border-accent pb-2 mono text-[11px] tracking-[.08em] text-foreground"><FileText className="size-3.5" /> {transcript ? 'Hide transcript' : 'View transcript'}</button>
        <span className="mono text-[10px] tracking-[.08em] text-muted-foreground">{source ? 'NATIVE HTML5 PLAYER / CAPTIONS CONFIGURED WHEN PROVIDED' : 'PLAYER READY FOR MP4 OR WEBM'}</span>
      </div>
      {transcript && <div className="mt-6 flex items-start gap-3 border hairline bg-background p-5 text-sm leading-6 text-muted-foreground"><X className="mt-1 size-4 shrink-0 text-accent" />Transcript will be available with the project presentation.</div>}

      <div className="mt-14 grid gap-12 lg:grid-cols-[.9fr_1.1fr]">
        <div><SectionLabel>Presentation Index</SectionLabel><div className="mt-6 divide-y hairline border-y hairline">{index.map(([id, title, detail]) => <div key={id} className="grid grid-cols-[2.5rem_7rem_1fr] gap-3 py-4 text-sm"><span className="mono text-[10px] text-muted-foreground">{id}</span><span className="font-medium">{title}</span><span className="text-muted-foreground">{detail}</span></div>)}</div></div>
        <div className="flex flex-wrap content-start gap-6 lg:justify-end"><ArrowLink href="/architecture">Explore architecture</ArrowLink><ArrowLink href="/runtime">Open runtime</ArrowLink><ArrowLink href="/research">Read research</ArrowLink></div>
      </div>
    </div>
  </section>
}

function Meta({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) { return <div className="border-b hairline p-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"><div className="mono text-[9px] tracking-[.12em] text-muted-foreground">{label}</div><div className={`mt-2 text-xs ${accent ? 'text-accent' : 'text-foreground'}`}>{value}</div></div> }
ნების

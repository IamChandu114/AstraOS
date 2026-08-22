'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowRight, Check, Circle, Menu, X } from 'lucide-react'
import { RuntimeStatus } from '@/components/runtime-status'

export const stages = [
  ['01', 'OBSERVE', 'Telemetry collector', 'CPU / memory / process signals'],
  ['02', 'ANALYZE', 'Workload intelligence', 'Classification and root-cause signals'],
  ['03', 'PREDICT', 'Pressure forecasting', 'Thermal and resource trend'],
  ['04', 'DECIDE', 'Policy generation', 'Risk-aware optimization planning'],
  ['05', 'ACT', 'Safe runtime action', 'Recommendations with constraints'],
  ['06', 'VERIFY', 'Optimization proof', 'Feedback and continuous adaptation'],
]

export function Header() {
  const [open, setOpen] = useState(false)
  const links = [['Runtime','/runtime'],['Architecture','/architecture'],['Experiments','/experiments'],['Research','/research'],['Benchmarks','/benchmarks'],['Docs','/documentation']]
  return <header className="relative z-20 border-b hairline">
    <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-8">
      <Link href="/" className="flex items-center gap-3" aria-label="AstraOS home"><span className="flex size-7 items-center justify-center border border-accent text-accent"><span className="size-2 bg-accent" /></span><span className="mono text-sm font-semibold tracking-[.22em]">ASTRAOS</span></Link>
      <nav className="hidden items-center gap-6 lg:flex">{links.map(([label, href]) => <Link key={href} href={href} className="mono text-[10px] tracking-[.1em] text-muted-foreground transition-colors hover:text-foreground">{label}</Link>)}{process.env.NEXT_PUBLIC_GITHUB_URL ? <a href={process.env.NEXT_PUBLIC_GITHUB_URL} className="mono inline-flex items-center gap-2 text-[10px] tracking-[.1em] text-foreground">GITHUB ↗</a> : <span className="mono text-[10px] tracking-[.1em] text-muted-foreground">SOURCE UNAVAILABLE</span>}</nav>
      <div className="flex items-center gap-5"><RuntimeStatus /><button className="lg:hidden" onClick={() => setOpen(!open)} aria-label={open ? 'Close navigation' : 'Open navigation'}>{open ? <X className="size-5" /> : <Menu className="size-5" />}</button></div>
    </div>
    {open && <nav className="border-t hairline px-5 py-4 lg:hidden">{links.map(([label, href]) => <Link onClick={() => setOpen(false)} key={href} href={href} className="block py-3 mono text-xs text-muted-foreground">{label}</Link>)}</nav>}
  </header>
}

export function Footer() { return <footer className="border-t hairline"><div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-10 lg:flex-row lg:items-end lg:justify-between lg:px-8"><div><div className="mono text-sm tracking-[.22em]">ASTRAOS</div><p className="mt-3 max-w-xs text-sm leading-6 text-muted-foreground">AI-native infrastructure intelligence for systems that need to reason about their future state.</p></div><div className="flex flex-wrap gap-x-5 gap-y-3 mono text-[10px] tracking-[.1em] text-muted-foreground">{[['Architecture','/architecture'],['Experiments','/experiments'],['Research','/research'],['Documentation','/documentation']].map(([l,h]) => <Link key={h} href={h} className="hover:text-foreground">{l}</Link>)}{process.env.NEXT_PUBLIC_GITHUB_URL ? <a href={process.env.NEXT_PUBLIC_GITHUB_URL} className="inline-flex items-center gap-1 hover:text-foreground">GitHub ↗</a> : <span aria-label="GitHub repository unavailable">GitHub unavailable</span>}</div><div className="mono text-[10px] text-muted-foreground">ENGINEERING RESEARCH PROJECT</div></div></footer> }

export function SectionLabel({ children, number }: { children: string; number?: string }) { return <div className="eyebrow flex items-center gap-3">{number && <span className="text-muted-foreground">{number}</span>}<span>{children}</span></div> }
export function ArrowLink({ href, children }: { href: string; children: string }) { return <Link href={href} className="group inline-flex items-center gap-2 border-b border-accent pb-2 mono text-[11px] tracking-[.08em] text-foreground">{children}<ArrowRight className="size-3 transition-transform group-hover:translate-x-1" /></Link> }
export function Status({ label, tone = 'muted' }: { label: string; tone?: 'accent'|'muted' }) { return <span className={`mono inline-flex items-center gap-2 text-[10px] tracking-[.1em] ${tone === 'accent' ? 'text-accent' : 'text-muted-foreground'}`}><Circle className="size-2 fill-current" />{label}</span> }
export function Shell({ children, current }: { children: React.ReactNode; current?: string }) { return <><Header /><main>{children}</main><Footer /></> }
export function Pipeline({ compact = false }: { compact?: boolean }) { return <div className={`grid ${compact ? 'grid-cols-2 sm:grid-cols-3' : 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6'} border-l hairline`}>{stages.map(([id, name, title, detail], i) => <div key={name} className="group relative border-b border-r hairline p-4 transition-colors hover:bg-muted"><div className="flex items-center justify-between"><span className="mono text-[10px] text-muted-foreground">{id}</span>{i < stages.length - 1 && <span className="hidden text-muted-foreground lg:block">→</span>}</div><div className="mt-8 text-xs font-semibold tracking-[.12em]">{name}</div><p className="mt-2 text-xs leading-5 text-muted-foreground">{compact ? title : detail}</p><div className="mt-5 h-px w-6 bg-accent transition-all group-hover:w-12" /></div>)}</div> }
export function Evidence({ title, status, detail }: { title: string; status: string; detail: string }) { return <div className="border hairline bg-card p-5"><div className="flex items-start justify-between gap-4"><span className="mono text-xs">{title}</span><Status label={status} tone={status === 'AVAILABLE' ? 'accent' : 'muted'} /></div><p className="mt-5 text-sm leading-6 text-muted-foreground">{detail}</p></div> }
export function CheckList({ items }: { items: string[] }) { return <ul className="space-y-3">{items.map(item => <li key={item} className="flex gap-3 text-sm leading-6 text-muted-foreground"><Check className="mt-1 size-4 shrink-0 text-accent" />{item}</li>)}</ul> }

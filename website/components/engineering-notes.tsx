import { ArrowUpRight } from 'lucide-react'
import { SectionLabel } from '@/components/astraos'

const engineeringNotes = [
  { number: '01', category: 'SYSTEMS', title: 'Why Modern Infrastructure Needs Systems That Can Reason About Future State', description: 'Why modern infrastructure needs to move beyond reactive monitoring and begin reasoning about future system state.', date: 'AUG 20, 2026', readingTime: '13 MIN READ', href: 'https://medium.com/@ca4443700/why-modern-infrastructure-needs-systems-that-can-reason-about-future-state-db3fa2d4a8cd?sharedUserId=ca4443700' },
  { number: '02', category: 'AI INFRASTRUCTURE', title: 'Building an AI-Native Infrastructure Runtime: Architecture, Telemetry, Prediction & Control', description: 'Inside the architecture behind AstraOS: telemetry, runtime intelligence, prediction, policy generation, and verification.', date: 'AUG 20, 2026', readingTime: '13 MIN READ', href: 'https://medium.com/@ca4443700/building-an-ai-native-infrastructure-runtime-architecture-telemetry-prediction-control-c2de8c84ed58?sharedUserId=ca4443700' },
  { number: '03', category: 'OBSERVABILITY', title: 'From Observation to Autonomous Optimization: Designing a Closed-Loop Intelligent Runtime', description: 'How AstraOS moves from observation and prediction toward constrained decisions, autonomous optimization, and continuous verification through a closed-loop runtime.', date: 'AUG 22, 2026', readingTime: '12 MIN READ', href: 'https://medium.com/@ca4443700/from-observation-to-autonomous-optimization-designing-a-closed-loop-intelligent-runtime-b2d2fb655140?sharedUserId=ca4443700' },
]

export function EngineeringNotes() {
  return (
    <section className="border-y hairline bg-card" aria-labelledby="engineering-notes-title">
      <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-24">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <SectionLabel number="05">ENGINEERING NOTES</SectionLabel>
            <h2 id="engineering-notes-title" className="mt-5 max-w-2xl text-3xl font-medium leading-tight tracking-[-.04em]">Engineering notes from the AstraOS runtime.</h2>
            <p className="mt-5 max-w-2xl text-sm leading-6 text-muted-foreground">Deep dives into AI-native infrastructure, systems engineering, observability, runtime intelligence, and the engineering decisions behind AstraOS.</p>
          </div>
        </div>
        <div className="mt-12 grid gap-3 lg:grid-cols-3">
          {engineeringNotes.map((article) => {
            const content = <><div className="flex items-start justify-between gap-4"><span className="mono text-[11px] text-accent">{article.number}</span><span className="mono text-[10px] tracking-[.08em] text-muted-foreground">{article.category}</span></div><h3 className="mt-12 text-xl font-medium tracking-[-.03em]">{article.title}</h3><p className="mt-4 min-h-12 text-sm leading-6 text-muted-foreground">{article.description}</p><div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t hairline pt-4 mono text-[10px] tracking-[.06em] text-muted-foreground"><span>{article.date} / {article.readingTime}</span><span className="inline-flex items-center gap-2">{article.href ? 'READ ARTICLE' : 'LINK UNAVAILABLE'} {article.href && <ArrowUpRight className="size-3" />}</span></div></>
            return article.href ? <a key={article.number} href={article.href} target="_blank" rel="noreferrer" aria-label={`${article.title} — opens in a new tab`} className="border hairline bg-background p-6 transition-colors hover:border-accent/60">{content}</a> : <article key={article.number} className="border hairline bg-background p-6" aria-label={`${article.title} — article in preparation`}>{content}</article>
          })}
        </div>
      </div>
    </section>
  )
}

export { engineeringNotes }

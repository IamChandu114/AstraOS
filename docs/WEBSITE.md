# AstraOS Professional Website

The `website/` app is a cinematic product and research showcase for AstraOS. It is separate from the live dashboard:

- Website: product story, architecture, engineering depth, benchmarks, demo framing, docs, and recruiter CTA.
- Dashboard: operational runtime control center for live telemetry and optimization state.

## Run

```powershell
cd website
npm run dev
```

Open:

```text
http://127.0.0.1:5174
```

## Data Sources

The website consumes real AstraOS runtime APIs when the backend is running:

- `GET /metrics?limit=120`
- `GET /elite/status`
- `GET /benchmarks`
- `GET /research-report`

If the backend or a host capability is unavailable, the website displays warming/offline/unavailable states instead of fake metrics.

## Sections Built

- Cinematic hero with animated infrastructure canvas
- Live system intelligence
- Architecture visualization
- Dashboard showcase
- AI optimization engine
- eBPF/kernel observability
- Distributed edge orchestration
- Performance benchmarks
- Self-healing infrastructure
- Research and engineering depth
- Demo video frame
- Tech stack
- GitHub/documentation links
- Contact/recruiter CTA

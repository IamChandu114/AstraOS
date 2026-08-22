import type { Metadata } from 'next'
import { BenchmarksContent } from '@/components/content'
export const metadata: Metadata = { title: 'Benchmarks — AstraOS', description: 'Evidence-first benchmark methodology for AstraOS infrastructure intelligence.' }
export default function Page(){ return <BenchmarksContent /> }

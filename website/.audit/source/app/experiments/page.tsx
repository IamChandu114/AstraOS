import type { Metadata } from 'next'
import { BenchmarksContent } from '@/components/content'
export const metadata: Metadata = { title: 'Experiments — AstraOS', description: 'Designed experiments and validation requirements for AstraOS systems research.' }
export default function Page(){ return <BenchmarksContent experiments /> }

import type { Metadata } from 'next'
import { SimpleContent } from '@/components/content'
export const metadata: Metadata = { title: 'Documentation — AstraOS', description: 'Technical documentation for the AstraOS runtime, telemetry, policies, and evidence model.' }
export default function Page(){ return <SimpleContent kind="docs" /> }

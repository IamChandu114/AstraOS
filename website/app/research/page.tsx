import type { Metadata } from 'next'
import { ResearchContent } from '@/components/content'
export const metadata: Metadata = { title: 'Research — AstraOS', description: 'An engineering research archive for AI-native infrastructure intelligence.' }
export default function Page(){ return <ResearchContent /> }

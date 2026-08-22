import type { Metadata } from 'next'
import { SimpleContent } from '@/components/content'
export const metadata: Metadata = { title: 'About — AstraOS', description: 'The motivation, principles, capabilities, and limitations behind AstraOS.' }
export default function Page(){ return <SimpleContent kind="about" /> }

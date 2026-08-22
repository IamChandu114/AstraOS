import { EngineeringNotes } from '@/components/engineering-notes'
import { Shell } from '@/components/astraos'

export const metadata = {
  title: 'Articles — AstraOS',
  description: 'Engineering notes from the AstraOS runtime.',
}

export default function ArticlesPage() {
  return (
    <Shell>
      <EngineeringNotes />
    </Shell>
  )
}

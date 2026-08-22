import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { JetBrains_Mono, Manrope } from 'next/font/google'
import './globals.css'

const manrope = Manrope({ subsets: ['latin'], variable: '--font-manrope' })
const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' })

export const metadata: Metadata = {
  title: 'AstraOS — AI-Native Infrastructure Intelligence',
  description: 'Observe system behavior, predict resource pressure, and verify optimization policies through a continuous runtime control loop.',
  generator: 'AstraOS',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#0a0c0d',
  userScalable: true,
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={`${manrope.variable} ${jetbrains.variable}`}><body className="antialiased">{children}{process.env.NODE_ENV === 'production' && <Analytics />}</body></html>
}

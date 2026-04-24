import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Axiom Picks — AI Sports Intelligence',
  description: 'Naive Bayes powered daily picks and backtesting for all major sports leagues.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg-primary text-txt-primary antialiased">
        {children}
      </body>
    </html>
  )
}

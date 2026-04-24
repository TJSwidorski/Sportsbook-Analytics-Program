import { DottedSurface } from '@/components/ui/dotted-surface'
import { Nav } from '@/components/Nav'
import { HeroSection } from '@/components/HeroSection'
import { PicksSection } from '@/components/PicksSection'

// Static date — picks are fetched client-side from the API
const TODAY = new Date().toISOString().split('T')[0]

export default function HomePage() {
  return (
    <>
      <DottedSurface />
      <Nav />

      <main className="relative min-h-screen pt-28 pb-20">
        <div className="max-w-7xl mx-auto px-6 space-y-16">
          <div
            className="animate-in-up"
            style={{ animationDelay: '0.1s' }}
          >
            <HeroSection date={TODAY} sportsCount={9} totalPicks={0} />
          </div>

          <div
            className="animate-in-up"
            style={{ animationDelay: '0.3s' }}
          >
            <PicksSection date={TODAY} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative border-t border-border-subtle/50 py-8">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <p className="text-xs font-mono-data text-txt-muted">
            AXIOM · Naive Bayes sports intelligence
          </p>
          <p className="text-xs font-mono-data text-txt-muted">
            Data: SportsBookReview.com
          </p>
        </div>
      </footer>
    </>
  )
}

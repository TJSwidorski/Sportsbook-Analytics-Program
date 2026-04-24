import { DottedSurface } from '@/components/ui/dotted-surface'
import { Nav } from '@/components/Nav'
import { BacktestTerminal } from '@/components/BacktestTerminal'

export default function BacktestPage() {
  return (
    <>
      <DottedSurface />
      <Nav />

      <main className="relative min-h-screen pt-28 pb-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="animate-in-up" style={{ animationDelay: '0.1s' }}>
            <BacktestTerminal />
          </div>
        </div>
      </main>

      <footer className="relative border-t border-border-subtle/50 py-8">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <p className="text-xs font-mono-data text-txt-muted">
            AXIOM · Walk-forward backtester — cache-only, no data leakage
          </p>
          <p className="text-xs font-mono-data text-txt-muted">
            Units: correct -200 → +0.5u · correct +150 → +1.5u · wrong → -1.0u
          </p>
        </div>
      </footer>
    </>
  )
}

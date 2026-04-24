'use client'

import { SportsOrbit } from './SportsOrbit'
import { Button } from './ui/button'
import Link from 'next/link'

interface HeroSectionProps {
  date: string
  sportsCount: number
  totalPicks: number
}

export function HeroSection({ date, sportsCount, totalPicks }: HeroSectionProps) {
  const formattedDate = new Date(date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })

  return (
    <section className="relative max-w-7xl mx-auto overflow-hidden rounded-3xl border border-border-subtle bg-bg-surface/40">
      <div className="flex items-center justify-between h-[28rem]">
        {/* Left: Text content */}
        <div className="w-1/2 pl-12 pr-8 z-10">
          {/* Date badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-elevated border border-border-subtle mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-mint animate-pulse-soft" />
            <span className="text-xs font-mono-data text-txt-muted uppercase tracking-widest">
              {formattedDate}
            </span>
          </div>

          <h1 className="font-display text-6xl font-semibold italic leading-tight text-txt-primary mb-2">
            Your picks
          </h1>
          <h1 className="font-display text-6xl font-semibold italic leading-tight text-gradient-mint mb-6">
            for today.
          </h1>

          <p className="text-sm text-txt-secondary max-w-sm mb-8 leading-relaxed">
            Naive Bayes model trained on historical moneyline data. Picks update
            daily as new odds are scraped.
          </p>

          {/* Stats row */}
          <div className="flex items-center gap-6 mb-8">
            <div>
              <p className="text-2xl font-display font-semibold text-mint">{sportsCount}</p>
              <p className="text-[10px] text-txt-muted uppercase tracking-widest font-mono-data">Sports active</p>
            </div>
            <div className="w-px h-8 bg-border-subtle" />
            <div>
              <p className="text-2xl font-display font-semibold text-royal">{totalPicks}</p>
              <p className="text-[10px] text-txt-muted uppercase tracking-widest font-mono-data">Games today</p>
            </div>
            <div className="w-px h-8 bg-border-subtle" />
            <div>
              <p className="text-2xl font-display font-semibold text-amber">NB</p>
              <p className="text-[10px] text-txt-muted uppercase tracking-widest font-mono-data">Model</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button size="lg">
              <a href="#picks">View Picks</a>
            </Button>
            <Button variant="secondary" size="lg" asChild>
              <Link href="/backtest">Backtest</Link>
            </Button>
          </div>
        </div>

        {/* Right: Sports orbit visualization */}
        <div className="w-1/2 h-full">
          <SportsOrbit />
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-bg-primary/60 to-transparent pointer-events-none" />
    </section>
  )
}

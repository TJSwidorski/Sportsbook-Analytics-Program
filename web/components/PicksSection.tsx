'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs'
import { MorphingCardStack, type PickCardData } from './ui/morphing-card-stack'

const SPORT_LABELS: Record<string, string> = {
  nba: 'NBA', nfl: 'NFL', nhl: 'NHL', mlb: 'MLB',
  mls: 'MLS', ncaaf: 'NCAAF', ncaab: 'NCAAB', wnba: 'WNBA', cfl: 'CFL',
}

interface RawPick {
  game_index: number
  pick: string
  confidence: number | null
  away_prob: number | null
  home_prob: number | null
  away_lines: string[]
  home_lines: string[]
}

interface AllPicksResponse {
  date: string
  sports: Record<string, RawPick[]>
  error?: string
}

function toCardData(sport: string, picks: RawPick[]): PickCardData[] {
  return picks.map((p) => ({
    id: `${sport}-${p.game_index}`,
    title: `Game ${p.game_index + 1}`,
    pick: p.pick,
    confidence: p.confidence,
    awayProb: p.away_prob,
    homeProb: p.home_prob,
    awayLines: p.away_lines,
    homeLines: p.home_lines,
  }))
}

export function PicksSection({ date }: { date: string }) {
  const [data, setData] = useState<AllPicksResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeSport, setActiveSport] = useState('nba')

  useEffect(() => {
    setLoading(true)
    fetch(`/api/picks/all?date=${date}`)
      .then((r) => r.json())
      .then((d: AllPicksResponse) => {
        setData(d)
        // Default to first sport that has picks
        const withPicks = Object.entries(d.sports ?? {}).find(([, picks]) => picks.length > 0)
        if (withPicks) setActiveSport(withPicks[0])
      })
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [date])

  const sports = data?.sports ?? {}
  const sportsWithPicks = Object.entries(sports).filter(([, picks]) => picks.length > 0)

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="w-8 h-8 rounded-full border-2 border-mint/30 border-t-mint animate-spin" />
        <p className="text-sm font-mono-data text-txt-muted">Loading picks…</p>
      </div>
    )
  }

  if (!data || sportsWithPicks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <span className="text-5xl font-display italic text-txt-muted">—</span>
        <p className="text-txt-muted text-sm font-mono-data">No picks available for this date.</p>
        <p className="text-txt-muted text-xs">Make sure the API server is running and the cache is populated.</p>
      </div>
    )
  }

  return (
    <section id="picks" className="max-w-7xl mx-auto">
      {/* Section header */}
      <div className="flex items-end justify-between mb-8">
        <div>
          <h2 className="font-display text-4xl font-semibold italic text-txt-primary">
            Today&apos;s Intelligence
          </h2>
          <p className="text-txt-secondary text-sm mt-1">
            {sportsWithPicks.length} sport{sportsWithPicks.length !== 1 ? 's' : ''} ·{' '}
            {sportsWithPicks.reduce((acc, [, picks]) => acc + picks.length, 0)} total games
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono-data text-txt-muted">
          <span className="inline-block w-2 h-2 rounded-full bg-mint" /> Win pick
          <span className="inline-block w-2 h-2 rounded-full bg-royal ml-2" /> Home pick
          <span className="inline-block w-2 h-2 rounded-full bg-border-def ml-2" /> No pick
        </div>
      </div>

      <Tabs value={activeSport} onValueChange={setActiveSport}>
        {/* Sport tabs */}
        <TabsList className="flex-wrap h-auto gap-1 mb-8">
          {sportsWithPicks.map(([sport, picks]) => (
            <TabsTrigger key={sport} value={sport} className="relative">
              {SPORT_LABELS[sport] ?? sport.toUpperCase()}
              <span className="ml-2 text-[9px] font-mono-data opacity-60">{picks.length}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Sport pick content */}
        {sportsWithPicks.map(([sport, picks]) => {
          const cards = toCardData(sport, picks)
          const strongPicks = picks.filter((p) => p.pick !== 'No Pick').length
          const avgConf = picks.reduce((s, p) => s + (p.confidence ?? 0), 0) / (picks.length || 1)

          return (
            <TabsContent key={sport} value={sport}>
              <div className="grid lg:grid-cols-[1fr_320px] gap-8">
                {/* Card stack */}
                <div className="flex items-start justify-center pt-4">
                  <MorphingCardStack cards={cards} defaultLayout="stack" />
                </div>

                {/* Stats sidebar */}
                <div className="space-y-4">
                  <div className="glass rounded-2xl p-5">
                    <h3 className="text-xs font-mono-data text-txt-muted uppercase tracking-widest mb-4">
                      {SPORT_LABELS[sport]} Summary
                    </h3>

                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-txt-secondary">Total games</span>
                        <span className="font-mono-data text-txt-primary font-medium">{picks.length}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-txt-secondary">Picks made</span>
                        <span className="font-mono-data text-mint font-medium">{strongPicks}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-txt-secondary">Avg confidence</span>
                        <span className="font-mono-data text-amber font-medium">
                          {(avgConf * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <div className="mt-5 pt-4 border-t border-border-subtle">
                      <p className="text-[10px] text-txt-muted uppercase tracking-widest mb-3">
                        Pick distribution
                      </p>
                      <div className="space-y-2">
                        {(['Away', 'Home', 'No Pick'] as const).map((pickType) => {
                          const count = picks.filter((p) => p.pick === pickType).length
                          const pct = picks.length ? (count / picks.length) * 100 : 0
                          const color = pickType === 'Away' ? '#00E896' : pickType === 'Home' ? '#3D8BFF' : '#3D5280'
                          return (
                            <div key={pickType}>
                              <div className="flex justify-between text-[10px] font-mono-data mb-1">
                                <span style={{ color }}>{pickType}</span>
                                <span className="text-txt-muted">{count}</span>
                              </div>
                              <div className="h-0.5 rounded-full bg-border-subtle">
                                <div
                                  className="h-full rounded-full transition-all duration-700"
                                  style={{ width: `${pct}%`, backgroundColor: color }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>

                  <div className="glass rounded-2xl p-5">
                    <p className="text-[10px] text-txt-muted uppercase tracking-widest mb-3">Model info</p>
                    <div className="space-y-2 text-xs font-mono-data">
                      <div className="flex justify-between">
                        <span className="text-txt-muted">Algorithm</span>
                        <span className="text-txt-secondary">Naive Bayes</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-txt-muted">Features</span>
                        <span className="text-txt-secondary">Moneyline odds</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-txt-muted">Training</span>
                        <span className="text-txt-secondary">60-day window</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          )
        })}
      </Tabs>
    </section>
  )
}

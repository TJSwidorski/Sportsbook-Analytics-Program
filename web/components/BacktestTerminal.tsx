'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Card, CardContent } from './ui/card'
import { BorderBeam } from './ui/border-beam'
import { TracingBeam } from './ui/tracing-beam'

const SPORTS = ['nba', 'nfl', 'nhl', 'mlb', 'mls', 'ncaaf', 'ncaab', 'wnba', 'cfl']
const SPORT_LABELS: Record<string, string> = {
  nba: 'NBA', nfl: 'NFL', nhl: 'NHL', mlb: 'MLB',
  mls: 'MLS', ncaaf: 'NCAAF', ncaab: 'NCAAB', wnba: 'WNBA', cfl: 'CFL',
}

interface GameLog {
  game_index: number
  date_or_week: string
  pick: string
  actual: string
  correct: boolean
  units: number
  away_lines: string[]
  home_lines: string[]
}

interface BacktestResponse {
  sport: string
  start: string
  end: string
  total_games: number
  games_picked: number
  correct_picks: number
  accuracy: number
  total_units: number
  game_log: GameLog[]
  error?: string
}

function StatCard({
  label,
  value,
  sub,
  color = '#00E896',
  beamColor = '#00E896',
}: {
  label: string
  value: string
  sub?: string
  color?: string
  beamColor?: string
}) {
  return (
    <Card className="relative overflow-hidden bg-bg-surface border-border-subtle">
      <BorderBeam colorFrom={beamColor} colorTo="#3D8BFF" duration={10} size={120} />
      <CardContent className="p-6">
        <p className="text-[10px] font-mono-data text-txt-muted uppercase tracking-widest mb-3">
          {label}
        </p>
        <p className="font-display text-4xl font-semibold italic" style={{ color }}>
          {value}
        </p>
        {sub && <p className="text-xs text-txt-muted mt-1 font-mono-data">{sub}</p>}
      </CardContent>
    </Card>
  )
}

function UnitsBadge({ units }: { units: number }) {
  const pos = units > 0
  return (
    <span
      className="text-xs font-mono-data font-semibold"
      style={{ color: pos ? '#00E896' : units === 0 ? '#3D5280' : '#FF3B5C' }}
    >
      {pos ? '+' : ''}{units.toFixed(2)}u
    </span>
  )
}

export function BacktestTerminal() {
  const [sport, setSport] = useState('nba')
  const [start, setStart] = useState('2024-01-01')
  const [end, setEnd] = useState('2024-12-31')
  const [window, setWindow] = useState('60')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BacktestResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const runBacktest = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const resp = await fetch('/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sport, start, end, training_window_days: parseInt(window) }),
      })
      const data: BacktestResponse = await resp.json()
      if (data.error) throw new Error(data.error)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const cumulativeUnits = result?.game_log.reduce<number[]>((acc, g) => {
    acc.push((acc[acc.length - 1] ?? 0) + g.units)
    return acc
  }, []) ?? []

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-elevated border border-border-subtle mb-4">
          <div className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse-soft" />
          <span className="text-xs font-mono-data text-txt-muted uppercase tracking-widest">Historical Analysis</span>
        </div>
        <h1 className="font-display text-6xl font-semibold italic text-txt-primary leading-tight">
          Backtest
          <span className="text-gradient-mint"> Terminal.</span>
        </h1>
        <p className="text-txt-secondary text-sm mt-3 max-w-lg">
          Walk-forward backtesting on cached historical data. Training window
          shifts daily — no data leakage.
        </p>
      </div>

      {/* Form */}
      <Card className="mb-8 bg-bg-surface border-border-subtle">
        <CardContent className="p-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <Label htmlFor="sport-select">Sport</Label>
              <select
                id="sport-select"
                value={sport}
                onChange={(e) => setSport(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-border-subtle bg-bg-elevated px-3 py-2 text-sm text-txt-primary font-mono-data focus:outline-none focus:border-mint/50 focus:ring-2 focus:ring-mint/20 transition-colors"
              >
                {SPORTS.map((s) => (
                  <option key={s} value={s} style={{ background: '#0D1525' }}>
                    {SPORT_LABELS[s]}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="start">Start Date</Label>
              <Input
                id="start"
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="end">End Date</Label>
              <Input
                id="end"
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="window">Training Window (days)</Label>
              <Input
                id="window"
                type="number"
                min="7"
                max="365"
                value={window}
                onChange={(e) => setWindow(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-6 flex items-center gap-4">
            <Button onClick={runBacktest} disabled={loading} size="lg">
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded-full border-2 border-bg-primary/30 border-t-bg-primary animate-spin" />
                  Running…
                </span>
              ) : (
                'Run Backtest'
              )}
            </Button>
            {result && (
              <p className="text-xs font-mono-data text-txt-muted">
                {result.total_games} games · {result.start} → {result.end}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl border border-crimson/30 bg-crimson/5 text-crimson text-sm font-mono-data">
          Error: {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-8 animate-in-up">
          {/* Stat cards with BorderBeam */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Accuracy"
              value={`${(result.accuracy * 100).toFixed(1)}%`}
              sub={`${result.correct_picks} / ${result.games_picked} picked`}
              color="#00E896"
              beamColor="#00E896"
            />
            <StatCard
              label="Total Units"
              value={`${result.total_units >= 0 ? '+' : ''}${result.total_units.toFixed(2)}`}
              sub="moneyline adjusted"
              color={result.total_units >= 0 ? '#00E896' : '#FF3B5C'}
              beamColor={result.total_units >= 0 ? '#00E896' : '#FF3B5C'}
            />
            <StatCard
              label="Games Picked"
              value={String(result.games_picked)}
              sub={`of ${result.total_games} total`}
              color="#FFA82E"
              beamColor="#FFA82E"
            />
            <StatCard
              label="Win Rate"
              value={
                result.games_picked > 0
                  ? `${((result.correct_picks / result.games_picked) * 100).toFixed(1)}%`
                  : '—'
              }
              sub={`${SPORT_LABELS[result.sport]}`}
              color="#3D8BFF"
              beamColor="#3D8BFF"
            />
          </div>

          {/* Cumulative units mini chart */}
          {cumulativeUnits.length > 1 && (
            <Card className="bg-bg-surface border-border-subtle overflow-hidden">
              <CardContent className="p-6">
                <p className="text-[10px] font-mono-data text-txt-muted uppercase tracking-widest mb-4">
                  Cumulative Units
                </p>
                <div className="relative h-24">
                  <svg
                    width="100%"
                    height="100%"
                    viewBox={`0 0 ${cumulativeUnits.length} 100`}
                    preserveAspectRatio="none"
                    className="overflow-visible"
                  >
                    <defs>
                      <linearGradient id="units-grad" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="#00E896" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#00E896" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    {(() => {
                      const min = Math.min(...cumulativeUnits)
                      const max = Math.max(...cumulativeUnits)
                      const range = max - min || 1
                      const pts = cumulativeUnits
                        .map((u, i) => `${i},${100 - ((u - min) / range) * 80 - 10}`)
                        .join(' ')
                      const fill = `${pts} ${cumulativeUnits.length - 1},100 0,100`
                      const finalColor = cumulativeUnits[cumulativeUnits.length - 1] >= 0 ? '#00E896' : '#FF3B5C'
                      return (
                        <>
                          <polygon points={fill} fill="url(#units-grad)" opacity="0.4" />
                          <polyline
                            points={pts}
                            fill="none"
                            stroke={finalColor}
                            strokeWidth="0.8"
                            vectorEffect="non-scaling-stroke"
                          />
                        </>
                      )
                    })()}
                  </svg>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Game log with TracingBeam */}
          {result.game_log.length > 0 && (
            <div>
              <h3 className="font-display text-2xl italic text-txt-primary mb-4">
                Game Log
                <span className="text-sm font-sans font-normal text-txt-muted ml-3">
                  {result.game_log.length} results
                </span>
              </h3>
              <TracingBeam>
                <div className="space-y-2 pl-4">
                  {/* Header */}
                  <div className="grid grid-cols-5 gap-4 py-2 px-4 text-[9px] font-mono-data text-txt-muted uppercase tracking-widest border-b border-border-subtle">
                    <span>Date / Week</span>
                    <span>Game</span>
                    <span>Pick</span>
                    <span>Actual</span>
                    <span className="text-right">Units</span>
                  </div>

                  {result.game_log.map((g, i) => (
                    <div
                      key={i}
                      className={`grid grid-cols-5 gap-4 py-2.5 px-4 rounded-lg text-sm transition-colors hover:bg-bg-elevated/50 ${
                        g.correct ? 'border-l-2 border-mint/30' : g.pick === 'No Pick' ? '' : 'border-l-2 border-crimson/20'
                      }`}
                    >
                      <span className="font-mono-data text-xs text-txt-muted">{g.date_or_week}</span>
                      <span className="font-mono-data text-xs text-txt-muted">#{g.game_index + 1}</span>
                      <span
                        className="font-mono-data text-xs font-medium"
                        style={{
                          color: g.pick === 'Away' ? '#00E896' : g.pick === 'Home' ? '#3D8BFF' : '#3D5280',
                        }}
                      >
                        {g.pick}
                      </span>
                      <span
                        className="font-mono-data text-xs"
                        style={{
                          color: g.actual === 'Away' ? '#00E896' : g.actual === 'Home' ? '#3D8BFF' : '#7A92C0',
                        }}
                      >
                        {g.actual}
                      </span>
                      <div className="text-right">
                        <UnitsBadge units={g.units} />
                      </div>
                    </div>
                  ))}
                </div>
              </TracingBeam>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

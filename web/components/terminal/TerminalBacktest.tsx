'use client'

import { useState } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { useBacktest, type BacktestGameLog } from '@/lib/use-backtest'
import { useHistory } from '@/lib/use-history'
import { SeasonGrid } from './SeasonGrid'
import { KpiStrip } from './KpiStrip'

interface Props {
  palette: Palette
}

const SPORTS = ['nba', 'nfl', 'nhl', 'mlb', 'mls', 'ncaaf', 'ncaab', 'wnba', 'cfl'] as const

function defaultDates(): { start: string; end: string } {
  const today = new Date()
  const end = new Date(today)
  end.setDate(end.getDate() - 1)
  const start = new Date(end)
  start.setDate(start.getDate() - 60)
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  }
}

function CompositeChart({ palette, log }: { palette: Palette; log: BacktestGameLog[] }) {
  const W = 800
  const H = 220
  const TOP_PAD = 10
  const BOT_PAD = 10
  const PLOT_H = H - TOP_PAD - BOT_PAD
  if (log.length === 0) {
    return (
      <div
        style={{
          height: H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: palette.muted,
          letterSpacing: 1,
        }}
      >
        NO DATA
      </div>
    )
  }
  let cum = 0
  const cumPts: { x: number; y: number; cum: number }[] = []
  log.forEach((g, i) => {
    cum += g.units
    cumPts.push({ x: i, y: cum, cum })
  })
  const maxV = Math.max(0, ...cumPts.map((p) => p.y))
  const minV = Math.min(0, ...cumPts.map((p) => p.y))
  const range = maxV - minV || 1
  const yFor = (v: number) => H - BOT_PAD - ((v - minV) / range) * PLOT_H
  const path = cumPts
    .map((p, i) => {
      const x = (i / (cumPts.length - 1 || 1)) * W
      return `${x.toFixed(1)},${yFor(p.y).toFixed(1)}`
    })
    .join(' ')
  const ticks = niceTicks(minV, maxV, 4)
  const zeroY = yFor(0)
  return (
    <div style={{ position: 'relative', height: '100%', paddingLeft: 36 }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: '100%' }} preserveAspectRatio="none">
        {ticks.map((v) => (
          <line
            key={v}
            x1="0"
            x2={W}
            y1={yFor(v)}
            y2={yFor(v)}
            stroke={palette.border}
            strokeWidth="1"
          />
        ))}
        {minV < 0 && maxV > 0 && (
          <line
            x1="0"
            x2={W}
            y1={zeroY}
            y2={zeroY}
            stroke={palette.muted}
            strokeWidth="1"
            strokeDasharray="4 4"
            opacity="0.7"
          />
        )}
        <polyline points={`0,${yFor(0)} ${path} ${W},${yFor(0)}`} fill={palette.accent} opacity="0.08" />
        <polyline points={path} fill="none" stroke={palette.accent} strokeWidth="1.5" />
      </svg>
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 32, pointerEvents: 'none' }}>
        {ticks.map((v) => {
          const pct = (yFor(v) / H) * 100
          const isZero = Math.abs(v) < 1e-9
          return (
            <div
              key={v}
              style={{
                position: 'absolute',
                right: 4,
                top: `${pct}%`,
                transform: 'translateY(-50%)',
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: isZero ? palette.text : palette.muted,
                fontWeight: isZero ? 600 : 400,
                letterSpacing: 0.5,
              }}
            >
              {formatUnitTick(v)}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function formatUnitTick(v: number): string {
  if (Math.abs(v) < 1e-9) return '0u'
  const sign = v > 0 ? '+' : ''
  if (Math.abs(v) >= 100) return `${sign}${v.toFixed(0)}u`
  return `${sign}${v.toFixed(1)}u`
}

function niceTicks(min: number, max: number, count: number): number[] {
  if (min === max) return [0]
  const range = max - min
  const rough = range / count
  const pow = Math.pow(10, Math.floor(Math.log10(rough)))
  const candidates = [1, 2, 2.5, 5, 10].map((c) => c * pow)
  const step = candidates.find((c) => range / c <= count + 1) ?? candidates[candidates.length - 1]
  const lo = Math.ceil(min / step) * step
  const out: number[] = []
  for (let v = lo; v <= max + step / 2; v += step) {
    out.push(Number(v.toFixed(6)))
  }
  if (min < 0 && max > 0 && !out.some((v) => Math.abs(v) < 1e-9)) {
    out.push(0)
    out.sort((a, b) => a - b)
  }
  return out
}

export function TerminalBacktest({ palette }: Props) {
  const { data: history } = useHistory()
  const dflt = defaultDates()
  const [sport, setSport] = useState<(typeof SPORTS)[number]>('nba')
  const [start, setStart] = useState(dflt.start)
  const [end, setEnd] = useState(dflt.end)
  const { status, result, error, run } = useBacktest()

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    run({ sport, start, end })
  }

  return (
    <div style={{ padding: '32px', maxWidth: 1376, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1.5,
            marginBottom: 6,
          }}
        >
          HISTORICAL BACKTEST / WALK-FORWARD
        </div>
        <h2 style={{ fontSize: 36, fontWeight: 500, margin: '0 0 12px', letterSpacing: -1 }}>
          Run a backtest. <span style={{ color: palette.muted }}>Every pick logged.</span>
        </h2>
        <p style={{ fontSize: 14, color: palette.muted, maxWidth: 640, lineHeight: 1.5 }}>
          Walk-forward training on cached scraped odds — flat 1u staking + fractional Kelly sizing.
          Cache must already cover the requested window (run <code>python seed_db.py</code> first).
        </p>
      </div>

      {history?.totals && (
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'space-between',
              marginBottom: 10,
              gap: 12,
              flexWrap: 'wrap',
            }}
          >
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 11,
                color: palette.muted,
                letterSpacing: 1.5,
              }}
            >
              ALL-TIME · EVERY CACHED SEASON
              {history.totals.earliest_year != null && (
                <span style={{ marginLeft: 12, color: palette.accent }}>
                  ● SINCE {history.totals.earliest_year}
                </span>
              )}
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: palette.muted,
                letterSpacing: 0.5,
              }}
              title="Aggregated across every season currently in backtest_history. Picks are merged in chronological order to compute the all-time max drawdown."
            >
              MERGED CHRONOLOGICALLY ACROSS SPORTS
            </div>
          </div>
          <KpiStrip
            palette={palette}
            cells={[
              {
                label: 'ALL-TIME PICKS',
                value: history.totals.games_picked.toLocaleString(),
                delta: `${history.totals.correct_picks.toLocaleString()} W`,
                color: 'blue',
              },
              {
                label: 'ALL-TIME WIN RATE',
                value:
                  history.totals.win_rate != null
                    ? `${(history.totals.win_rate * 100).toFixed(1)}%`
                    : '—',
                color: 'accent',
              },
              {
                label: 'ALL-TIME UNITS',
                value: `${history.totals.flat_units >= 0 ? '+' : ''}${history.totals.flat_units.toFixed(2)}`,
                delta: history.totals.roi_flat != null
                  ? `${(history.totals.roi_flat * 100 >= 0 ? '+' : '')}${(history.totals.roi_flat * 100).toFixed(2)}% ROI`
                  : undefined,
                color: history.totals.flat_units >= 0 ? 'accent' : 'danger',
              },
              {
                label: 'ALL-TIME MAX DD',
                value:
                  history.totals.max_drawdown != null
                    ? `-${Math.abs(history.totals.max_drawdown).toFixed(2)}u`
                    : '—',
                color: 'blue',
              },
            ]}
          />
        </div>
      )}

      <form
        onSubmit={onSubmit}
        style={{
          background: palette.surface,
          border: `1px solid ${palette.border}`,
          padding: 24,
          marginBottom: 24,
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr) auto',
          gap: 16,
          alignItems: 'end',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 10,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 6,
            }}
          >
            SPORT
          </div>
          <select
            value={sport}
            onChange={(e) => setSport(e.target.value as (typeof SPORTS)[number])}
            style={{
              width: '100%',
              padding: '8px 10px',
              background: palette.surface2,
              color: palette.text,
              border: `1px solid ${palette.border2}`,
              fontFamily: FONT_MONO,
              fontSize: 13,
            }}
          >
            {SPORTS.map((s) => (
              <option key={s} value={s}>
                {s.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        <div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 10,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 6,
            }}
          >
            START
          </div>
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 10px',
              background: palette.surface2,
              color: palette.text,
              border: `1px solid ${palette.border2}`,
              fontFamily: FONT_MONO,
              fontSize: 13,
            }}
          />
        </div>
        <div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 10,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 6,
            }}
          >
            END
          </div>
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 10px',
              background: palette.surface2,
              color: palette.text,
              border: `1px solid ${palette.border2}`,
              fontFamily: FONT_MONO,
              fontSize: 13,
            }}
          />
        </div>
        <div />
        <button
          type="submit"
          disabled={status === 'running'}
          style={{
            padding: '10px 18px',
            background: palette.text,
            color: palette.bg,
            border: 'none',
            fontFamily: FONT_MONO,
            fontSize: 12,
            letterSpacing: 1,
            cursor: status === 'running' ? 'wait' : 'pointer',
            opacity: status === 'running' ? 0.6 : 1,
          }}
        >
          {status === 'running' ? 'RUNNING…' : 'RUN BACKTEST'}
        </button>
      </form>

      {status === 'error' && (
        <div
          style={{
            padding: 16,
            marginBottom: 24,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.danger,
            border: `1px solid ${palette.border}`,
            background: palette.surface,
          }}
        >
          ERROR: {error}
        </div>
      )}

      {result && (
        <>
          <div style={{ marginBottom: 24 }}>
            <KpiStrip
              palette={palette}
              cells={[
                {
                  label: 'PICKED',
                  value: result.games_picked.toLocaleString(),
                  delta: `${result.total_games} games`,
                  color: 'blue',
                },
                {
                  label: 'WIN RATE',
                  value:
                    result.accuracy != null
                      ? `${(result.accuracy * 100).toFixed(1)}%`
                      : '—',
                  delta: `${result.correct_picks} W`,
                  color: 'accent',
                },
                {
                  label: 'FLAT UNITS',
                  value: `${result.flat_units >= 0 ? '+' : ''}${result.flat_units.toFixed(2)}`,
                  color: result.flat_units >= 0 ? 'accent' : 'danger',
                },
                {
                  label: 'KELLY UNITS',
                  value: `${result.kelly_units >= 0 ? '+' : ''}${result.kelly_units.toFixed(2)}`,
                  color: result.kelly_units >= 0 ? 'accent' : 'danger',
                },
                {
                  label: 'ROI (FLAT)',
                  value:
                    result.games_picked > 0
                      ? `${
                          (result.flat_units / result.games_picked) * 100 >= 0 ? '+' : ''
                        }${((result.flat_units / result.games_picked) * 100).toFixed(1)}%`
                      : '—',
                  color: 'accent',
                },
                {
                  label: 'MAX DRAWDOWN',
                  value:
                    result.max_drawdown != null
                      ? `-${Math.abs(result.max_drawdown).toFixed(2)}`
                      : '—',
                  color: 'blue',
                },
              ]}
            />
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: palette.muted,
                marginTop: 8,
                letterSpacing: 0.5,
              }}
              title="The furthest the cumulative-units curve dipped below the starting bankroll of zero during this window. A 0u drawdown means the curve never went negative; a large drawdown means the bankroll spent time underwater before recovering."
            >
              MAX DRAWDOWN = furthest the unit curve dipped below 0u during this run.
            </div>
          </div>

          <div
            style={{
              background: palette.surface,
              border: `1px solid ${palette.border}`,
              padding: 24,
              marginBottom: 24,
            }}
          >
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  color: palette.muted,
                  letterSpacing: 1.5,
                  marginBottom: 4,
                }}
              >
                CUMULATIVE UNITS / {result.start} → {result.end}
              </div>
              <div style={{ fontSize: 22, fontWeight: 500, fontFamily: FONT_MONO }}>
                {result.flat_units >= 0 ? '+' : ''}
                {result.flat_units.toFixed(2)}
              </div>
            </div>
            <div style={{ height: 220 }}>
              <CompositeChart palette={palette} log={result.game_log} />
            </div>
          </div>
        </>
      )}

      <div style={{ marginBottom: 12 }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1.5,
          }}
        >
          PER-SPORT / LAST COMPLETED SEASON
        </div>
      </div>
      <SeasonGrid palette={palette} rows={history?.sports ?? []} />
    </div>
  )
}

'use client'

import { useMemo, useState } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { usePerformance } from '@/lib/use-performance'
import { KpiStrip } from './KpiStrip'
import { UnitsChart } from './UnitsChart'

interface Props {
  palette: Palette
}

const RANGE_OPTIONS: { label: string; days: number }[] = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
]

const MODEL_OPTIONS: { label: string; value: string }[] = [
  { label: 'LOGREG', value: 'logreg' },
  { label: 'LOGREG V2', value: 'logreg_v2' },
]

export function TerminalHistory({ palette }: Props) {
  const [rangeIdx, setRangeIdx] = useState(1)
  const [modelIdx, setModelIdx] = useState(1)
  const days = RANGE_OPTIONS[rangeIdx].days
  const model = MODEL_OPTIONS[modelIdx].value
  const { status, series, sports, totals, error } = usePerformance(days, model)

  const winRate = totals?.win_rate != null ? `${(totals.win_rate * 100).toFixed(1)}%` : '—'
  const games = totals?.games_picked != null ? totals.games_picked.toLocaleString() : '—'
  const flat = totals?.flat_units != null
    ? `${totals.flat_units >= 0 ? '+' : ''}${totals.flat_units.toFixed(1)}`
    : '—'
  const kelly = totals?.kelly_units != null
    ? `${totals.kelly_units >= 0 ? '+' : ''}${totals.kelly_units.toFixed(2)}`
    : '—'
  const maxDD = totals?.max_drawdown != null
    ? `-${Math.abs(totals.max_drawdown).toFixed(1)}`
    : '—'

  const sportRows = useMemo(
    () =>
      sports.map((r) => ({
        sport: r.sport,
        picks: r.games_picked,
        winRate: r.games_picked ? (r.correct_picks / r.games_picked) * 100 : 0,
        units: r.flat_units,
        maxDrawdown: r.max_drawdown,
      })),
    [sports],
  )

  const isEmpty = status === 'ready' && sports.length === 0

  return (
    <div style={{ padding: '32px', maxWidth: 1376, margin: '0 auto' }}>
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          gap: 16,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 6,
            }}
          >
            ROLLING BACKTEST / LAST {RANGE_OPTIONS[rangeIdx].label}
          </div>
          <h2 style={{ fontSize: 36, fontWeight: 500, margin: 0, letterSpacing: -1 }}>
            Recent Performance
          </h2>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              marginTop: 8,
              maxWidth: 720,
              lineHeight: 1.55,
            }}
          >
            {MODEL_OPTIONS[modelIdx].label} — what this model would have done over the
            last {days} days, replayed against real prices. Recomputed daily, no future data.
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', gap: 8, fontFamily: FONT_MONO, fontSize: 11 }}>
            {RANGE_OPTIONS.map((opt, i) => (
              <button
                key={opt.label}
                onClick={() => setRangeIdx(i)}
                style={{
                  padding: '6px 12px',
                  background: i === rangeIdx ? palette.text : palette.surface,
                  color: i === rangeIdx ? palette.bg : palette.muted,
                  border: `1px solid ${palette.border2}`,
                  cursor: 'pointer',
                  letterSpacing: 1,
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, fontFamily: FONT_MONO, fontSize: 11 }}>
            {MODEL_OPTIONS.map((opt, i) => (
              <button
                key={opt.value}
                onClick={() => setModelIdx(i)}
                style={{
                  padding: '6px 12px',
                  background: i === modelIdx ? palette.accent : palette.surface,
                  color: i === modelIdx ? palette.bg : palette.muted,
                  border: `1px solid ${i === modelIdx ? palette.accent : palette.border2}`,
                  cursor: 'pointer',
                  letterSpacing: 1,
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <KpiStrip
          palette={palette}
          cells={[
            { label: 'WIN RATE', value: winRate, color: 'accent' },
            { label: 'PICKS', value: games, color: 'blue' },
            { label: 'UNITS WON', value: flat, color: 'accent' },
            { label: 'KELLY UNITS', value: kelly, color: 'accent' },
            { label: 'MAX DRAWDOWN', value: maxDD, color: 'blue' },
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
          title="Max drawdown is the worst peak-to-trough loss the model would have seen during this window. Compare it to UNITS WON: a small drawdown vs a large profit means a smoother ride."
        >
          MAX DRAWDOWN = worst peak-to-trough loss in the window. Compare to UNITS WON to gauge volatility.
        </div>
      </div>

      {isEmpty && (
        <div
          style={{
            padding: 16,
            marginBottom: 24,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            border: `1px solid ${palette.border}`,
            background: palette.surface,
          }}
        >
          {error ?? 'No in-season sports right now, or the cache is still warming up.'}
        </div>
      )}

      <div style={{ marginBottom: 24 }}>
        <UnitsChart
          palette={palette}
          series={series}
          label={`CUMULATIVE UNITS / LAST ${RANGE_OPTIONS[rangeIdx].label}`}
        />
      </div>

      <div
        style={{
          background: palette.surface,
          border: `1px solid ${palette.border}`,
          padding: 24,
        }}
      >
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1.5,
            marginBottom: 20,
          }}
        >
          BY SPORT / LAST {RANGE_OPTIONS[rangeIdx].label}
        </div>
        {sportRows.length === 0 ? (
          <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: palette.muted }}>
            NO IN-SEASON SPORTS IN THIS WINDOW.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 18 }}>
            {sportRows.map((s) => {
              const unitsFormatted = `${s.units >= 0 ? '+' : ''}${s.units.toFixed(1)}u`
              const drawdownFormatted = `-${Math.abs(s.maxDrawdown).toFixed(1)}u`
              return (
                <div key={s.sport}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 6,
                      fontFamily: FONT_MONO,
                      fontSize: 12,
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{s.sport.toUpperCase()}</span>
                    <span style={{ color: palette.muted }}>
                      {s.picks.toLocaleString()} picks
                    </span>
                  </div>
                  <div style={{ height: 4, background: palette.surface2, position: 'relative', marginBottom: 6 }}>
                    <div
                      style={{
                        position: 'absolute',
                        inset: 0,
                        width: `${Math.max(0, Math.min(100, (s.winRate - 50) * 5))}%`,
                        background: palette.accent,
                      }}
                    />
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontFamily: FONT_MONO,
                      fontSize: 10,
                      color: palette.muted,
                      letterSpacing: 0.5,
                    }}
                  >
                    <span>WIN <span style={{ color: palette.accent }}>{s.winRate.toFixed(1)}%</span></span>
                    <span>UNITS <span style={{ color: s.units >= 0 ? palette.accent : palette.danger }}>{unitsFormatted}</span></span>
                    <span>MAX DD <span style={{ color: palette.blue }}>{drawdownFormatted}</span></span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

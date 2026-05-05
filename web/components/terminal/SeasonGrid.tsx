'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import type { HistorySportRow } from '@/lib/use-history'

interface Props {
  palette: Palette
  rows: HistorySportRow[]
}

function seasonLabel(year: number, sport: string): string {
  const dateBased = ['nba', 'nhl', 'mls'].includes(sport)
  if (dateBased) return `${year - 1}-${String(year).slice(-2)}`
  return String(year)
}

function miniEquity(units: number, palette: Palette, seed: number) {
  const W = 120
  const H = 32
  const N = 20
  const pts: string[] = []
  for (let k = 0; k < N; k++) {
    const x = (k / (N - 1)) * W
    const v = (units / 80) * (k / (N - 1)) + Math.sin(k * 1.7 + seed) * 0.05
    const y = 28 - v * 24
    pts.push(`${x.toFixed(1)},${Math.max(2, Math.min(30, y)).toFixed(1)}`)
  }
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      <polyline points={pts.join(' ')} fill="none" stroke={palette.accent} strokeWidth="1.5" />
    </svg>
  )
}

export function SeasonGrid({ palette, rows }: Props) {
  return (
    <div
      style={{
        background: palette.surface,
        border: `1px solid ${palette.border}`,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          borderBottom: `1px solid ${palette.border}`,
          fontFamily: FONT_MONO,
          fontSize: 10,
          color: palette.muted,
          letterSpacing: 1,
        }}
      >
        <div style={{ padding: '12px 20px' }}>SPORT / SEASON</div>
        <div style={{ padding: '12px 20px' }}>PICKS</div>
        <div style={{ padding: '12px 20px' }}>WIN RATE</div>
        <div style={{ padding: '12px 20px' }}>UNITS</div>
        <div style={{ padding: '12px 20px' }}>ROI</div>
        <div style={{ padding: '12px 20px' }} title="Worst peak-to-trough loss during this season">MAX DD</div>
        <div style={{ padding: '12px 20px' }}>EQUITY CURVE</div>
      </div>
      {rows.length === 0 && (
        <div
          style={{
            padding: 32,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
          }}
        >
          NO BACKTEST HISTORY YET. Run `python backtest_history.py` to populate this view.
        </div>
      )}
      {rows.map((s, i) => {
        const win = s.win_rate != null ? `${(s.win_rate * 100).toFixed(1)}%` : '—'
        const roi = s.roi_flat != null ? `${(s.roi_flat * 100).toFixed(1)}%` : '—'
        const units = s.flat_units
        return (
          <div
            key={`${s.sport}-${s.season_year}`}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, 1fr)',
              borderBottom: i < rows.length - 1 ? `1px solid ${palette.border}` : 'none',
              fontFamily: FONT_MONO,
              fontSize: 14,
            }}
          >
            <div style={{ padding: '20px', fontWeight: 600 }}>
              {s.sport.toUpperCase()} {seasonLabel(s.season_year, s.sport)}
            </div>
            <div style={{ padding: '20px', color: palette.muted }}>
              {s.games_picked.toLocaleString()}
            </div>
            <div style={{ padding: '20px' }}>{win}</div>
            <div style={{ padding: '20px', color: units >= 0 ? palette.accent : palette.danger }}>
              {units >= 0 ? '+' : ''}
              {units.toFixed(1)}
            </div>
            <div style={{ padding: '20px' }}>{roi}</div>
            <div style={{ padding: '20px', color: palette.blue }}>
              {s.max_drawdown != null ? `-${Math.abs(s.max_drawdown).toFixed(1)}` : '—'}
            </div>
            <div style={{ padding: '20px', display: 'flex', alignItems: 'center' }}>
              {miniEquity(units, palette, i)}
            </div>
          </div>
        )
      })}
    </div>
  )
}

'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import type { PerformancePoint } from '@/lib/use-performance'

interface Props {
  palette: Palette
  series: PerformancePoint[]
  height?: number
  label?: string
}

export function UnitsChart({ palette, series, height = 280, label = 'CUMULATIVE UNITS' }: Props) {
  const points = series.length > 0 ? series : []
  const cumValues = points.map((p) => p.cum_units)
  const maxV = points.length ? Math.max(0, ...cumValues) : 0
  const minV = points.length ? Math.min(0, ...cumValues) : 0
  const range = maxV - minV || 1
  const last = points[points.length - 1]
  const labelValue = last ? last.cum_units : 0

  const W = 800
  const H = 280
  const TOP_PAD = 10
  const BOT_PAD = 10
  const PLOT_H = H - TOP_PAD - BOT_PAD
  const yFor = (v: number) => H - BOT_PAD - ((v - minV) / range) * PLOT_H
  const xy = (i: number, v: number) => {
    const x = points.length > 1 ? (i / (points.length - 1)) * W : W / 2
    return { x, y: yFor(v) }
  }
  const path = points
    .map((p, i) => {
      const { x, y } = xy(i, p.cum_units)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  const ticks = niceTicks(minV, maxV, 4)
  const zeroY = yFor(0)

  return (
    <div
      style={{
        background: palette.surface,
        border: `1px solid ${palette.border}`,
        padding: 24,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 4,
            }}
          >
            {label}
          </div>
          <div style={{ fontSize: 22, fontWeight: 500, fontFamily: FONT_MONO }}>
            {labelValue >= 0 ? '+' : ''}
            {labelValue.toFixed(2)}
          </div>
        </div>
      </div>
      <div style={{ height, position: 'relative', paddingLeft: 36 }}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: '100%' }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="units-line" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stopColor={palette.blue} />
              <stop offset="100%" stopColor={palette.accent} />
            </linearGradient>
          </defs>
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
          {points.length > 1 && minV < 0 && maxV > 0 && (
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
          {points.length > 1 && (
            <>
              <polyline points={path} fill="none" stroke="url(#units-line)" strokeWidth="1.5" />
              <polyline
                points={`0,${yFor(0)} ${path} ${W},${yFor(0)}`}
                fill={palette.accent}
                opacity="0.08"
              />
              {points.map((p, i) => {
                const { x, y } = xy(i, p.cum_units)
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="2"
                    fill={palette.surface}
                    stroke={i % 4 === 0 ? palette.blue : palette.accent}
                    strokeWidth="1"
                  />
                )
              })}
            </>
          )}
        </svg>
        {points.length > 1 && (
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              bottom: 0,
              width: 32,
              pointerEvents: 'none',
            }}
          >
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
                  {formatTick(v)}
                </div>
              )
            })}
          </div>
        )}
        {points.length === 0 && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
            }}
          >
            NO DATA YET
          </div>
        )}
      </div>
    </div>
  )
}

function formatTick(v: number): string {
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

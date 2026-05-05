'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import type { PerformancePoint } from '@/lib/use-performance'

interface Props {
  palette: Palette
  series: PerformancePoint[]
  height?: number
}

export function SparklineChart({ palette, series, height = 80 }: Props) {
  const W = 400
  const H = 80
  const cum = series.map((d) => d.cum_units)
  const max = series.length ? Math.max(0, ...cum) : 1
  const min = series.length ? Math.min(0, ...cum) : 0
  const range = max - min || 1
  const yFor = (v: number) => 75 - ((v - min) / range) * 65
  const xy = (i: number, v: number) => {
    const x = series.length > 1 ? (i / (series.length - 1)) * W : W / 2
    return `${x.toFixed(1)},${yFor(v).toFixed(1)}`
  }
  const path = series.map((p, i) => xy(i, p.cum_units)).join(' ')
  const zeroY = yFor(0)

  return (
    <div style={{ height, position: 'relative' }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: '100%' }} preserveAspectRatio="none">
        <defs>
          <linearGradient id="spark-line" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor={palette.blue} />
            <stop offset="100%" stopColor={palette.accent} />
          </linearGradient>
        </defs>
        {series.length > 1 && (
          <>
            <line
              x1="0"
              x2={W}
              y1={zeroY}
              y2={zeroY}
              stroke={palette.muted}
              strokeWidth="0.75"
              strokeDasharray="3 3"
              opacity="0.6"
            />
            <polyline points={path} fill="none" stroke="url(#spark-line)" strokeWidth="1.5" />
            <polyline
              points={`0,75 ${path} ${W},75`}
              fill={palette.accent}
              opacity="0.1"
            />
          </>
        )}
      </svg>
      {series.length > 1 && (
        <span
          style={{
            position: 'absolute',
            left: 2,
            top: `${(zeroY / H) * 100}%`,
            transform: 'translateY(-110%)',
            fontFamily: FONT_MONO,
            fontSize: 9,
            color: palette.muted,
            letterSpacing: 0.5,
            pointerEvents: 'none',
          }}
        >
          0u
        </span>
      )}
    </div>
  )
}

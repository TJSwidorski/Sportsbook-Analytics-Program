'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'

export interface KpiCell {
  label: string
  value: string
  delta?: string
  color?: 'accent' | 'blue' | 'danger' | 'muted'
}

interface Props {
  palette: Palette
  cells: KpiCell[]
}

export function KpiStrip({ palette, cells }: Props) {
  const colorOf = (key: KpiCell['color']) => {
    switch (key) {
      case 'blue': return palette.blue
      case 'danger': return palette.danger
      case 'muted': return palette.muted
      default: return palette.accent
    }
  }
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${cells.length}, 1fr)`,
        gap: 1,
        background: palette.border,
        border: `1px solid ${palette.border}`,
      }}
    >
      {cells.map((c, i) => (
        <div key={i} style={{ background: palette.surface, padding: 20 }}>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 10,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 8,
            }}
          >
            {c.label}
          </div>
          <div
            style={{
              fontSize: 28,
              fontWeight: 500,
              fontFamily: FONT_MONO,
              letterSpacing: -0.5,
            }}
          >
            {c.value}
          </div>
          {c.delta && (
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: colorOf(c.color),
                marginTop: 4,
              }}
            >
              {c.delta}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

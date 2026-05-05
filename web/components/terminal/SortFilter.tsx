'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'

export type SortMode = 'EDGE' | 'CONFIDENCE' | 'LONGSHOT' | 'FAVORITE'

const LABELS: Record<SortMode, string> = {
  EDGE: 'HIGHEST EDGE',
  CONFIDENCE: 'HIGHEST CONFIDENCE',
  LONGSHOT: 'HIGHEST ODDS',
  FAVORITE: 'LOWEST ODDS',
}

interface Props {
  palette: Palette
  value: SortMode
  onChange: (v: SortMode) => void
}

export function SortFilter({ palette, value, onChange }: Props) {
  const options: SortMode[] = ['EDGE', 'CONFIDENCE', 'LONGSHOT', 'FAVORITE']
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span
        style={{
          fontFamily: FONT_MONO,
          fontSize: 10,
          color: palette.muted,
          letterSpacing: 1.5,
        }}
      >
        SORT
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as SortMode)}
        style={{
          padding: '6px 10px',
          background: palette.surface,
          color: palette.text,
          border: `1px solid ${palette.border2}`,
          fontFamily: FONT_MONO,
          fontSize: 11,
          letterSpacing: 1,
          cursor: 'pointer',
        }}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {LABELS[opt]}
          </option>
        ))}
      </select>
    </div>
  )
}

/**
 * Convert an American-odds line string (e.g. "+150", "-200") into decimal odds.
 * Decimal odds rank long-shots highest (e.g. +250 → 3.5, -200 → 1.5). Returns
 * null when the input is not parseable so callers can sort it to the bottom.
 */
export function americanToDecimal(line: string | null | undefined): number | null {
  if (!line) return null
  const trimmed = line.trim().replace(/^\+/, '')
  const n = Number(trimmed)
  if (!Number.isFinite(n) || n === 0) return null
  if (n > 0) return 1 + n / 100
  return 1 + 100 / Math.abs(n)
}

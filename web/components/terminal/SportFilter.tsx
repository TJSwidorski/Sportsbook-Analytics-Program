'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { SportMark } from './SportMark'

interface Props {
  palette: Palette
  options: string[]
  value: string
  onChange: (v: string) => void
}

export function SportFilter({ palette, options, value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: 8, fontFamily: FONT_MONO, fontSize: 11, flexWrap: 'wrap' }}>
      {options.map((t) => {
        const active = t === value
        const isAll = t === 'ALL'
        return (
          <button
            key={t}
            onClick={() => onChange(t)}
            style={{
              padding: '6px 12px',
              background: active ? palette.text : palette.surface,
              color: active ? palette.bg : palette.muted,
              border: `1px solid ${palette.border2}`,
              cursor: 'pointer',
              letterSpacing: 1,
              fontFamily: FONT_MONO,
              fontSize: 11,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {!isAll && <SportMark palette={palette} sport={t.toLowerCase()} size={12} />}
            {t}
          </button>
        )
      })}
    </div>
  )
}

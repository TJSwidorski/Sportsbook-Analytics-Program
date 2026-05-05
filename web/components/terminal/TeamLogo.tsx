'use client'

import { useEffect, useState } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { teamLogoUrl } from '@/lib/logos'

interface Props {
  palette: Palette
  sport: string
  abbr: string
  team?: string
  size?: number
}

export function TeamLogo({ palette, sport, abbr, team, size = 40 }: Props) {
  const url = teamLogoUrl(sport, abbr)
  const [errored, setErrored] = useState(false)

  useEffect(() => {
    setErrored(false)
  }, [url])

  const showImg = url && !errored
  const monogramText = (abbr || team || '').slice(0, 3).toUpperCase() || '—'

  return (
    <div
      style={{
        width: size,
        height: size,
        background: palette.surface2,
        border: `1px solid ${palette.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      {showImg ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt={team || abbr}
          width={size}
          height={size}
          loading="lazy"
          decoding="async"
          onError={() => setErrored(true)}
          style={{
            width: size,
            height: size,
            objectFit: 'contain',
            display: 'block',
          }}
        />
      ) : (
        <span
          style={{
            fontFamily: FONT_MONO,
            fontSize: Math.max(9, Math.round(size * 0.28)),
            fontWeight: 600,
            letterSpacing: 0.5,
            color: palette.muted,
          }}
        >
          {monogramText}
        </span>
      )}
    </div>
  )
}

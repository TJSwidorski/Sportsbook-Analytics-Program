'use client'

import { useState } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { sportLogoUrl } from '@/lib/logos'

interface Props {
  palette: Palette
}

const LEAGUES: { sport: string; label: string }[] = [
  { sport: 'nba', label: 'NBA' },
  { sport: 'nfl', label: 'NFL' },
  { sport: 'nhl', label: 'NHL' },
  { sport: 'mlb', label: 'MLB' },
  { sport: 'mls', label: 'MLS' },
  { sport: 'ncaaf', label: 'NCAAF' },
  { sport: 'ncaab', label: 'NCAAB' },
  { sport: 'wnba', label: 'WNBA' },
  { sport: 'cfl', label: 'CFL' },
]

export function SportsLeaguesSlider({ palette }: Props) {
  const items = [...LEAGUES, ...LEAGUES]

  return (
    <div
      style={{
        background: palette.surface,
        border: `1px solid ${palette.border}`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 20px 12px',
          borderBottom: `1px solid ${palette.border}`,
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: palette.muted,
          letterSpacing: 1.5,
        }}
      >
        <span>◆ COVERAGE / NINE LEAGUES</span>
        <span style={{ color: palette.accent }}>● MONEYLINE</span>
      </div>

      <div
        className="axiom-leagues-track"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 0,
          width: 'max-content',
          animation: 'axiom-marquee 36s linear infinite',
          padding: '20px 0',
        }}
      >
        {items.map((league, i) => (
          <LeagueTile
            key={`${league.sport}-${i}`}
            sport={league.sport}
            label={league.label}
            palette={palette}
          />
        ))}
      </div>

      <FadeEdge palette={palette} side="left" />
      <FadeEdge palette={palette} side="right" />
    </div>
  )
}

function LeagueTile({
  sport,
  label,
  palette,
}: {
  sport: string
  label: string
  palette: Palette
}) {
  const url = sportLogoUrl(sport)
  const [errored, setErrored] = useState(false)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 10,
        width: 140,
        padding: '0 8px',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {url && !errored ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={url}
            alt={`${label} logo`}
            width={48}
            height={48}
            loading="lazy"
            decoding="async"
            onError={() => setErrored(true)}
            style={{
              width: 48,
              height: 48,
              objectFit: 'contain',
            }}
          />
        ) : (
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
            }}
          >
            {label}
          </span>
        )}
      </div>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 10,
          letterSpacing: 1.5,
          color: palette.muted,
        }}
      >
        {label}
      </div>
    </div>
  )
}

function FadeEdge({
  palette,
  side,
}: {
  palette: Palette
  side: 'left' | 'right'
}) {
  return (
    <div
      style={{
        position: 'absolute',
        top: 36,
        bottom: 0,
        [side]: 0,
        width: 96,
        pointerEvents: 'none',
        background:
          side === 'left'
            ? `linear-gradient(to right, ${palette.surface} 10%, transparent 100%)`
            : `linear-gradient(to left, ${palette.surface} 10%, transparent 100%)`,
      }}
    />
  )
}

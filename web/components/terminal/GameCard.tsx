'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { TeamLogo } from './TeamLogo'
import { SportMark } from './SportMark'

export interface GameCardData {
  sport: string
  league: string
  away: string
  home: string
  awayAbbr: string
  homeAbbr: string
  time: string
  pick: string
  confidence: number
  confidenceTier: 'HIGH' | 'MODERATE' | 'LEAN' | null
  edge: string
  edgeValue: number | null
  units: string
  isNoBet: boolean
}

interface Props {
  g: GameCardData
  palette: Palette
  onClick?: () => void
}

export function GameCard({ g, palette, onClick }: Props) {
  const negativeEdge = g.edgeValue != null && g.edgeValue < 0
  const pickColor = g.isNoBet
    ? palette.muted
    : negativeEdge
    ? palette.danger
    : palette.accent
  const edgeColor = g.edgeValue == null
    ? palette.text
    : g.edgeValue >= 0
    ? palette.accent
    : palette.danger

  return (
    <div
      onClick={onClick}
      style={{
        background: palette.surface,
        border: `1px solid ${palette.border}`,
        padding: 16,
        position: 'relative',
        cursor: onClick ? 'pointer' : 'default',
        backdropFilter: 'blur(10px)',
        boxShadow: g.isNoBet
          ? `0 0 0 1px ${palette.border}`
          : `0 0 0 1px ${palette.border}, 0 8px 24px -12px ${palette.accent}33`,
        opacity: g.isNoBet ? 0.78 : 1,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: -1,
          background: g.isNoBet
            ? 'transparent'
            : `radial-gradient(circle at 50% -20%, ${palette.accent}22, transparent 60%)`,
          pointerEvents: 'none',
        }}
      />
      <div style={{ position: 'relative' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontFamily: FONT_MONO,
            fontSize: 10,
            color: palette.muted,
            letterSpacing: 1,
            marginBottom: 14,
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <SportMark palette={palette} sport={g.sport} size={12} />
            {g.league}
          </span>
          <span>{g.time}</span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            alignItems: 'center',
            gap: 8,
            marginBottom: 14,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <TeamLogo palette={palette} sport={g.sport} abbr={g.awayAbbr} team={g.away} size={36} />
            <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
              {g.awayAbbr}
            </div>
          </div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 10,
              color: palette.muted,
              letterSpacing: 1,
            }}
          >
            @
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <TeamLogo palette={palette} sport={g.sport} abbr={g.homeAbbr} team={g.home} size={36} />
            <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, letterSpacing: 1 }}>
              {g.homeAbbr}
            </div>
          </div>
        </div>

        <div style={{ fontSize: 11, color: palette.muted, marginBottom: 12, fontFamily: FONT_MONO }}>
          {g.away} · {g.home}
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
          }}
        >
          <div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: palette.muted,
                letterSpacing: 1,
                marginBottom: 4,
              }}
            >
              {g.isNoBet ? 'DECISION' : 'BET'}
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: g.isNoBet ? 13 : 15,
                color: pickColor,
                fontWeight: 600,
                letterSpacing: g.isNoBet ? 1.5 : 0,
              }}
            >
              {g.pick}
            </div>
            {g.isNoBet ? (
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 9,
                  color: palette.muted,
                  marginTop: 2,
                  letterSpacing: 0.5,
                }}
              >
                MARKET FAIR
              </div>
            ) : null}
          </div>
          <div style={{ textAlign: 'right' }}>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: palette.muted,
                letterSpacing: 1,
                marginBottom: 4,
              }}
              title="Expected profit per $1 wagered, given our model's probability vs the posted odds. Negative means expected loss."
            >
              EDGE
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 15,
                fontWeight: 600,
                color: edgeColor,
              }}
            >
              {g.edge}
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 9,
                color: palette.muted,
                marginTop: 2,
                letterSpacing: 0.5,
              }}
            >
              per $1 bet
            </div>
          </div>
        </div>
        <div
          style={{
            marginTop: 14,
            height: 2,
            background: palette.surface2,
            position: 'relative',
            opacity: g.isNoBet ? 0.5 : 1,
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              width: `${Math.max(0, Math.min(100, g.confidence))}%`,
              background: g.isNoBet ? palette.muted : palette.accent,
            }}
          />
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 4,
            fontFamily: FONT_MONO,
            fontSize: 9,
            color: palette.muted,
            letterSpacing: 1,
          }}
        >
          <span title="How sure our model is. HIGH = strong signal; LEAN = barely above coin-flip.">
            CONFIDENCE
          </span>
          <span>
            {g.confidenceTier && !g.isNoBet ? `${g.confidenceTier} · ` : ''}
            {g.confidence}%
          </span>
        </div>
      </div>
    </div>
  )
}

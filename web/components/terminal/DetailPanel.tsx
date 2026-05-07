'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import type { RawPick } from '@/lib/use-upcoming-picks'
import { confidenceTier } from '@/lib/pick-adapter'
import { TeamLogo } from './TeamLogo'
import { SportMark } from './SportMark'

interface Props {
  palette: Palette
  pick: RawPick
  sport: string
  gameTime?: string
  onClose: () => void
}

// Kept for potential future "opening line" feature — index 0 of lines arrays
// const OPENING_LINE_LABEL = 'Open'

const SB_DOMAINS: Record<string, string> = {
  DraftKings: 'draftkings.com',
  FanDuel: 'fanduel.com',
  BetMGM: 'betmgm.com',
  Caesars: 'caesars.com',
  'Caesars Sportsbook': 'caesars.com',
  PointsBet: 'pointsbet.com',
  Unibet: 'unibet.com',
  BetRivers: 'betrivers.com',
  WynnBet: 'wynnbet.com',
  Barstool: 'barstool.com',
  'Barstool Sports': 'barstool.com',
  bet365: 'bet365.com',
  Betway: 'betway.com',
  'Hard Rock': 'hardrock.bet',
  'Hard Rock Bet': 'hardrock.bet',
  BookiePro: 'bookiepro.com',
  Bodog: 'bodog.com',
  '5Dimes': '5dimes.eu',
  'Golden Nugget': 'goldennugget.com',
  Tipico: 'tipico.com',
  Pinnacle: 'pinnacle.com',
  'ESPN BET': 'espnbet.com',
  Fliff: 'getfliff.com',
  Fanatics: 'fanatics.com',
}

function bookDomain(sb: string): string | null {
  return SB_DOMAINS[sb] ?? null
}

function impliedFromMoneyline(line: string): number | null {
  const trimmed = line.trim()
  if (!trimmed || trimmed === '—') return null
  const sign = trimmed[0]
  const numStr = trimmed.replace(/[^0-9.]/g, '')
  if (!numStr) return null
  const n = parseFloat(numStr)
  if (!Number.isFinite(n) || n <= 0) return null
  if (sign === '-') return n / (n + 100)
  return 100 / (n + 100)
}

interface SbRow {
  sb: string
  awayLine: string
  homeLine: string
  domain: string | null
}

export function DetailPanel({ palette, pick, sport, gameTime, onClose }: Props) {
  const awayAbbr = pick.away_abbr || (pick.away_team ?? '?').slice(0, 3).toUpperCase()
  const homeAbbr = pick.home_abbr || (pick.home_team ?? '?').slice(0, 3).toUpperCase()
  const teamLabel = pick.pick === 'Away' ? awayAbbr : pick.pick === 'Home' ? homeAbbr : pick.pick
  const teamFullName =
    pick.pick === 'Away' ? (pick.away_team ?? awayAbbr)
    : pick.pick === 'Home' ? (pick.home_team ?? homeAbbr)
    : null
  const evRaw = pick.ev != null && Number.isFinite(pick.ev) ? pick.ev : null
  const isNoBet = pick.pick === 'No Pick' || !pick.pick || (evRaw != null && evRaw < 0)

  const pickLabel = isNoBet
    ? 'NO BET'
    : pick.bet_line
    ? `${teamLabel} ${pick.bet_line}`
    : teamLabel
  const conf = pick.confidence != null ? Math.round(pick.confidence * 100) : 0
  const tier = isNoBet ? null : confidenceTier(conf)
  const units = pick.unit_size != null ? (pick.unit_size * 100).toFixed(1) : '0.0'
  const evPct = evRaw != null ? evRaw * 100 : null
  const ev = evPct == null ? '—' : `${evPct >= 0 ? '+' : ''}${evPct.toFixed(1)}%`
  const homeProb = pick.home_prob != null ? `${(pick.home_prob * 100).toFixed(1)}%` : '—'
  const awayProb = pick.away_prob != null ? `${(pick.away_prob * 100).toFixed(1)}%` : '—'

  const pickColor = isNoBet
    ? palette.muted
    : evPct != null && evPct < 0
    ? palette.danger
    : palette.accent
  const edgeColor = evPct == null
    ? palette.text
    : evPct >= 0
    ? palette.accent
    : palette.danger

  const analystNote = isNoBet
    ? `The market is paying less than our model thinks is fair. Expected loss per $1 wagered: ${
        evPct != null ? `$${Math.abs(evPct / 100).toFixed(2)}` : 'unknown'
      }. We don't recommend a bet here.`
    : `Our model gives the ${teamFullName ?? teamLabel} a higher chance to win than the market is paying${
        pick.bet_line ? `. We're betting them at ${pick.bet_line}.` : '.'
      }`

  // Build sportsbook rows — skip "Open" (index 0 / label 'Open') since it's the opening line
  const hasSbNames = (pick.sportsbooks?.length ?? 0) > 0
  const pickedSide = pick.pick === 'Away' ? 'away' : pick.pick === 'Home' ? 'home' : null

  const sbRows: SbRow[] = hasSbNames
    ? (pick.sportsbooks ?? []).reduce<SbRow[]>((acc, sb, i) => {
        if (sb === 'Open') return acc
        const awayLine = pick.away_lines?.[i] ?? '—'
        const homeLine = pick.home_lines?.[i] ?? '—'
        acc.push({ sb, awayLine, homeLine, domain: bookDomain(sb) })
        return acc
      }, [])
    : []

  const bestSbIdx =
    pickedSide && pick.bet_line
      ? sbRows.findIndex((r) =>
          pickedSide === 'away' ? r.awayLine === pick.bet_line : r.homeLine === pick.bet_line,
        )
      : -1

  return (
    <div
      style={{
        background: palette.surface,
        border: `1px solid ${palette.border}`,
        padding: 24,
        height: 'fit-content',
        position: 'sticky',
        top: 0,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1.5,
          }}
        >
          PICK DETAIL
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: palette.muted,
            cursor: 'pointer',
            fontSize: 18,
            lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: palette.muted,
          letterSpacing: 1,
          marginBottom: 16,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <SportMark palette={palette} sport={sport} size={12} />
        {sport.toUpperCase()} / {gameTime ?? 'TBD'}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <TeamLogo palette={palette} sport={sport} abbr={awayAbbr} team={pick.away_team} size={48} />
        <div style={{ fontSize: 26, fontWeight: 500, letterSpacing: -0.5 }}>
          {pick.away_team ?? awayAbbr}
        </div>
      </div>
      <div style={{ fontSize: 13, color: palette.muted, fontFamily: FONT_MONO, margin: '8px 0 8px 60px' }}>@</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <TeamLogo palette={palette} sport={sport} abbr={homeAbbr} team={pick.home_team} size={48} />
        <div style={{ fontSize: 26, fontWeight: 500, letterSpacing: -0.5 }}>
          {pick.home_team ?? homeAbbr}
        </div>
      </div>

      <div
        style={{
          background: palette.surface2,
          border: `1px solid ${palette.border}`,
          borderLeft: `2px solid ${isNoBet ? palette.muted : palette.blue}`,
          padding: 20,
          marginBottom: 20,
          opacity: isNoBet ? 0.85 : 1,
        }}
      >
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: isNoBet ? palette.muted : palette.blue,
            letterSpacing: 1,
            marginBottom: 8,
          }}
        >
          ◆ {isNoBet ? 'DECISION' : 'RECOMMENDATION'}
        </div>
        <div
          style={{
            fontSize: 32,
            fontFamily: FONT_MONO,
            color: pickColor,
            fontWeight: 600,
            marginBottom: 4,
          }}
        >
          {pickLabel}
        </div>
        {isNoBet ? (
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
              marginTop: 4,
            }}
          >
            MARKET PRICED FAIRLY — STAND DOWN
          </div>
        ) : null}
        <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
          <div>
            <div
              style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, letterSpacing: 1 }}
              title="Recommended bet size as a percentage of bankroll (Kelly-sized)."
            >
              UNITS
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 16, fontWeight: 600 }}>{units}u</div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 9, color: palette.muted, marginTop: 2 }}>
              of bankroll
            </div>
          </div>
          <div>
            <div
              style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, letterSpacing: 1 }}
              title="How much we expect to win (or lose, if negative) per $1 wagered."
            >
              EDGE
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 16, fontWeight: 600, color: edgeColor }}>
              {ev}
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 9, color: palette.muted, marginTop: 2 }}>
              per $1 bet
            </div>
          </div>
          <div>
            <div
              style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, letterSpacing: 1 }}
              title="How sure the model is. HIGH = strong signal, LEAN = barely above 50/50."
            >
              CONFIDENCE
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 16, fontWeight: 600 }}>{conf}%</div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 9, color: palette.muted, marginTop: 2 }}>
              {tier ?? '—'}
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1,
            marginBottom: 6,
          }}
        >
          WIN PROBABILITY (OUR MODEL)
        </div>
        <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, marginBottom: 12 }}>
          Our estimate of each team&apos;s chance to win this game.
        </div>
        {[
          { k: `${awayAbbr} win`, v: pick.away_prob ?? 0, label: awayProb, color: palette.blue },
          { k: `${homeAbbr} win`, v: pick.home_prob ?? 0, label: homeProb, color: palette.accent },
        ].map((s) => (
          <div key={s.k} style={{ marginBottom: 10 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 11,
                fontFamily: FONT_MONO,
                marginBottom: 4,
              }}
            >
              <span style={{ color: palette.muted }}>{s.k}</span>
              <span>{s.label}</span>
            </div>
            <div style={{ height: 2, background: palette.surface2, position: 'relative' }}>
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: `${Math.round(s.v * 100)}%`,
                  background: s.color,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Sportsbook odds table */}
      {sbRows.length > 0 ? (
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
              marginBottom: 6,
            }}
          >
            SPORTSBOOK ODDS
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, marginBottom: 10 }}>
            Current moneylines across books.
            {bestSbIdx >= 0 && (
              <span style={{ color: palette.accent }}> Highlighted = where we&apos;re taking the bet.</span>
            )}
          </div>

          {/* Column headers */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '16px 1fr 88px 88px',
              gap: '2px 8px',
              alignItems: 'center',
              paddingBottom: 6,
              marginBottom: 2,
              borderBottom: `1px solid ${palette.border}`,
            }}
          >
            <div />
            <div style={{ fontFamily: FONT_MONO, fontSize: 9, color: palette.muted, letterSpacing: 1 }}>
              BOOK
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 9,
                color: palette.muted,
                letterSpacing: 1,
                textAlign: 'right',
              }}
            >
              {awayAbbr}
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 9,
                color: palette.muted,
                letterSpacing: 1,
                textAlign: 'right',
              }}
            >
              {homeAbbr}
            </div>
          </div>

          {/* Book rows */}
          {sbRows.map((row, idx) => {
            const isBest = idx === bestSbIdx
            const awayImpl = impliedFromMoneyline(row.awayLine)
            const homeImpl = impliedFromMoneyline(row.homeLine)
            return (
              <div
                key={row.sb}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '16px 1fr 88px 88px',
                  gap: '2px 8px',
                  alignItems: 'center',
                  padding: '5px 6px',
                  marginLeft: -6,
                  marginRight: -6,
                  background: isBest ? `${palette.accent}15` : 'transparent',
                  borderLeft: isBest ? `2px solid ${palette.accent}` : '2px solid transparent',
                }}
              >
                {/* favicon */}
                <div style={{ width: 16, height: 16, display: 'flex', alignItems: 'center' }}>
                  {row.domain ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`https://www.google.com/s2/favicons?domain=${row.domain}&sz=16`}
                      width={14}
                      height={14}
                      alt=""
                      style={{ borderRadius: 2, opacity: 0.85 }}
                      onError={(e) => {
                        ;(e.currentTarget as HTMLImageElement).style.display = 'none'
                      }}
                    />
                  ) : null}
                </div>

                {/* sportsbook name */}
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    color: isBest ? palette.text : palette.muted,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {row.sb}
                </div>

                {/* away line */}
                <div style={{ fontFamily: FONT_MONO, fontSize: 11, textAlign: 'right' }}>
                  <span
                    style={{
                      color: isBest && pickedSide === 'away' ? palette.accent : palette.text,
                      fontWeight: isBest && pickedSide === 'away' ? 600 : 400,
                    }}
                  >
                    {row.awayLine}
                  </span>
                  {awayImpl != null && (
                    <span style={{ color: palette.muted, fontSize: 9, display: 'block' }}>
                      {(awayImpl * 100).toFixed(1)}%
                    </span>
                  )}
                </div>

                {/* home line */}
                <div style={{ fontFamily: FONT_MONO, fontSize: 11, textAlign: 'right' }}>
                  <span
                    style={{
                      color: isBest && pickedSide === 'home' ? palette.accent : palette.text,
                      fontWeight: isBest && pickedSide === 'home' ? 600 : 400,
                    }}
                  >
                    {row.homeLine}
                  </span>
                  {homeImpl != null && (
                    <span style={{ color: palette.muted, fontSize: 9, display: 'block' }}>
                      {(homeImpl * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (pick.away_lines?.length || pick.home_lines?.length) ? (
        /* Fallback: no sportsbook names — show raw lines */
        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
              marginBottom: 6,
            }}
          >
            POSTED MONEYLINES
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: palette.muted, marginBottom: 12 }}>
            What sportsbooks are paying. &quot;Implied&quot; = the win probability baked into each price.
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 11 }}>
            <div style={{ color: palette.muted, marginBottom: 4 }}>{awayAbbr}</div>
            <div style={{ marginBottom: 12 }}>
              {(pick.away_lines ?? []).length
                ? (pick.away_lines ?? []).map((line) => {
                    const implied = impliedFromMoneyline(line)
                    return (
                      <div
                        key={line}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '2px 0',
                        }}
                      >
                        <span>{line}</span>
                        <span style={{ color: palette.muted }}>
                          {implied != null ? `${(implied * 100).toFixed(1)}% implied` : '—'}
                        </span>
                      </div>
                    )
                  })
                : '—'}
            </div>
            <div style={{ color: palette.muted, marginBottom: 4 }}>{homeAbbr}</div>
            <div>
              {(pick.home_lines ?? []).length
                ? (pick.home_lines ?? []).map((line) => {
                    const implied = impliedFromMoneyline(line)
                    return (
                      <div
                        key={line}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '2px 0',
                        }}
                      >
                        <span>{line}</span>
                        <span style={{ color: palette.muted }}>
                          {implied != null ? `${(implied * 100).toFixed(1)}% implied` : '—'}
                        </span>
                      </div>
                    )
                  })
                : '—'}
            </div>
          </div>
        </div>
      ) : null}

      <div
        style={{
          background: palette.surface2,
          padding: 16,
          fontFamily: FONT_MONO,
          fontSize: 12,
          lineHeight: 1.55,
          color: palette.text,
          borderLeft: `2px solid ${isNoBet ? palette.muted : palette.blue}`,
        }}
      >
        <div style={{ color: palette.muted, fontSize: 10, letterSpacing: 1, marginBottom: 6 }}>
          WHY THIS CALL
        </div>
        {analystNote}
      </div>
    </div>
  )
}

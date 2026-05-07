'use client'

import { useMemo } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO, FONT_SANS } from '@/lib/palette'
import { useHistory } from '@/lib/use-history'
import { usePerformance } from '@/lib/use-performance'
import { useUpcomingPicks } from '@/lib/use-upcoming-picks'
import { GameCard } from './GameCard'
import { SparklineChart } from './SparklineChart'
import { SportsLeaguesSlider } from './SportsLeaguesSlider'
import { rawPickToGameCard, flattenUpcoming } from '@/lib/pick-adapter'

interface Props {
  palette: Palette
}

export function TerminalHome({ palette }: Props) {
  const today = new Date().toISOString().slice(0, 10)
  const { data: history } = useHistory()
  const { series } = usePerformance(30)
  const { data: upcoming } = useUpcomingPicks(today)

  const totals = history?.totals ?? null
  const teaserPicks = useMemo(() => {
    if (!upcoming) return []
    const all = flattenUpcoming(upcoming.sports)
    const live = all.filter((item) => {
      const ev = item.raw.ev
      const pick = item.raw.pick
      return (
        pick !== 'No Pick' &&
        !!pick &&
        ev != null &&
        Number.isFinite(ev) &&
        ev > 0
      )
    })
    live.sort((a, b) => (b.raw.ev ?? 0) - (a.raw.ev ?? 0))
    return live.slice(0, 4)
  }, [upcoming])

  const winRate = totals?.win_rate != null ? `${(totals.win_rate * 100).toFixed(1)}%` : '—'
  const flatUnits = totals?.flat_units != null
    ? `${totals.flat_units >= 0 ? '+' : ''}${totals.flat_units.toFixed(1)}`
    : '—'
  const picksTracked = totals?.games_picked != null ? totals.games_picked.toLocaleString() : '—'
  const last30 = series.length > 0 ? series[series.length - 1].cum_units : 0
  const last30Label = `30D · ${last30 >= 0 ? '+' : ''}${last30.toFixed(1)}u`
  const sinceLabel = totals?.earliest_year != null
    ? `SINCE ${totals.earliest_year}`
    : 'TRANSPARENT'

  return (
    <div style={{ padding: '48px 32px 80px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 2,
            marginBottom: 16,
          }}
        >
          ◆ DATA-DRIVEN SPORTS PICKS / EST. 2024
        </div>
        <h1
          style={{
            fontSize: 72,
            lineHeight: 0.95,
            fontWeight: 500,
            letterSpacing: -2,
            margin: '0 0 28px',
            maxWidth: 920,
            fontFamily: FONT_SANS,
          }}
        >
          The market is wrong
          <br />
          <span style={{ color: palette.muted }}>more often than you think.</span>
        </h1>
        <p
          style={{
            fontSize: 17,
            lineHeight: 1.5,
            color: palette.muted,
            maxWidth: 620,
            margin: '0 0 40px',
          }}
        >
          We run every sportsbook moneyline through our model and surface the games where
          the price doesn&apos;t match the real probability. Daily picks across nine leagues,
          public results, no hype.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 1,
            background: palette.border,
            border: `1px solid ${palette.border}`,
            marginBottom: 32,
          }}
        >
          {[
            { k: 'WIN RATE', v: winRate, sub: 'of picks won, all-time', trend: '', color: palette.accent },
            { k: 'UNITS WON', v: flatUnits, sub: 'profit at $1 per pick', trend: last30Label, color: palette.accent },
            { k: 'PICKS TRACKED', v: picksTracked, sub: 'every pick logged publicly', trend: sinceLabel, color: palette.blue },
          ].map((m, i) => (
            <div
              key={i}
              style={{ background: palette.surface, padding: '32px 28px', position: 'relative' }}
            >
              <div
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 11,
                  color: palette.muted,
                  letterSpacing: 1.5,
                  marginBottom: 12,
                }}
              >
                {m.k}
              </div>
              <div
                style={{
                  fontSize: 56,
                  fontWeight: 500,
                  fontFamily: FONT_MONO,
                  lineHeight: 1,
                  marginBottom: 8,
                  letterSpacing: -1,
                }}
              >
                {m.v}
              </div>
              <div style={{ fontSize: 12, color: palette.muted, fontFamily: FONT_MONO }}>{m.sub}</div>
              {m.trend && (
                <div
                  style={{
                    position: 'absolute',
                    top: 28,
                    right: 28,
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    color: m.color,
                    padding: '2px 6px',
                    border: `1px solid ${m.color}`,
                  }}
                >
                  {m.trend}
                </div>
              )}
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 56 }}>
          <SportsLeaguesSlider palette={palette} />
        </div>

        <div
          style={{
            background: palette.surface,
            border: `1px solid ${palette.border}`,
            borderLeft: `2px solid ${palette.accent}`,
            padding: 36,
            marginBottom: 32,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.accent,
              letterSpacing: 1.5,
              marginBottom: 8,
            }}
          >
            02 / HOW IT WORKS
          </div>
          <div
            style={{
              fontSize: 26,
              fontWeight: 500,
              lineHeight: 1.3,
              marginBottom: 28,
              letterSpacing: -0.4,
            }}
          >
            <span style={{ color: palette.blue }}>Built on years</span> of past games.
          </div>

          <Section palette={palette} title="What this site does">
            We watch the sportsbooks. Our model estimates how likely each team is to win,
            based on years of past games and how the betting public has priced similar
            matchups. When the sportsbook is offering a worse price than the model thinks
            the team deserves, we publish a pick. When it isn&apos;t, we say so — those
            games show up as <strong>NO BET</strong>.
          </Section>

          <Section palette={palette} title="How to read a pick card">
            <ul style={liStyle(palette)}>
              <li><strong>BET</strong> — the team and price we like (e.g. <code>BOS -120</code>).</li>
              <li><strong>EDGE</strong> — how much we expect to win, on average, per $1 wagered. <code>+5.0%</code> means we expect five cents of profit per dollar long-term. Negative means expected loss; that&apos;s why we say NO BET.</li>
              <li><strong>CONFIDENCE</strong> — how sure the model is. <code>HIGH</code> = strong signal, <code>LEAN</code> = barely above 50/50.</li>
              <li><strong>UNITS</strong> — what fraction of your bankroll the model would risk on this game (Kelly-sized). <code>1.0u</code> ≈ 1% of bankroll.</li>
            </ul>
          </Section>

          <Section palette={palette} title='What does "units" mean?'>
            Sports bettors talk in units instead of dollars because everyone&apos;s bankroll
            is different. One unit is whatever you decide a normal bet looks like — say
            $50 or $100. <code>+12.4 units</code> over a season means you&apos;d be up
            12.4× that base bet, regardless of dollar amount.
          </Section>

          <Section palette={palette} title='Why some games say "NO BET"'>
            If our model thinks a team has a 55% chance to win but the sportsbook is
            pricing them at a 60% chance, betting them is a long-run loss — even if they
            win that night. We don&apos;t force picks just to have something to publish.
            Roughly 40–60% of slates end up as NO BET on a given day, depending on the
            league.
          </Section>

          <Section palette={palette} title="A note on responsible betting">
            No model wins every day. Even profitable strategies have months that go
            sideways. Only bet money you&apos;re prepared to lose, set limits, and
            don&apos;t chase. If betting stops being fun, take a break — or call
            1-800-GAMBLER.
          </Section>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
              fontFamily: FONT_MONO,
              fontSize: 11,
              marginTop: 24,
            }}
          >
            {['MULTI-MODEL', 'SMART STAKING', 'TESTED ON PAST SEASONS', 'FULLY TRANSPARENT'].map((t, i) => (
              <div
                key={t}
                style={{
                  padding: '6px 10px',
                  background: palette.surface2,
                  color: palette.muted,
                  letterSpacing: 1,
                  borderLeft: `2px solid ${i % 2 ? palette.blue : palette.accent}`,
                }}
              >
                {i % 2 ? '◆' : '●'} {t}
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            background: palette.surface,
            border: `1px solid ${palette.border}`,
            padding: 32,
            marginBottom: 56,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1.5,
              marginBottom: 20,
            }}
          >
            03 / TRANSPARENCY
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 500,
              lineHeight: 1.3,
              marginBottom: 20,
              letterSpacing: -0.3,
            }}
          >
            Every pick logged. Wins and losses.
          </div>
          <SparklineChart palette={palette} series={series} />
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
            }}
          >
            <span>30D PERFORMANCE</span>
            <span style={{ color: palette.accent }}>{last30Label}</span>
          </div>
        </div>

        <div
          style={{
            marginBottom: 24,
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
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
            04 / TODAY&apos;S BOARD
            <span style={{ color: palette.accent, marginLeft: 12 }}>
              ● TOP {teaserPicks.length} BY EDGE
            </span>
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: palette.muted }}>
            VIEW ALL →
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {teaserPicks.map((item, i) => {
            const card = rawPickToGameCard(item.raw, item.sport, item.bucket === 'tomorrow' ? 'TOMORROW' : 'TODAY')
            return (
              <GameCard
                key={`${item.sport}-${item.raw.game_index}-${i}`}
                g={card}
                palette={palette}
              />
            )
          })}
          {teaserPicks.length === 0 && (
            <div
              style={{
                gridColumn: 'span 4',
                padding: 24,
                fontFamily: FONT_MONO,
                fontSize: 12,
                color: palette.muted,
                border: `1px solid ${palette.border}`,
                background: palette.surface,
                textAlign: 'center',
              }}
            >
              Our model hasn&apos;t found any profitable games today.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({
  palette,
  title,
  children,
}: {
  palette: Palette
  title: string
  children: React.ReactNode
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: palette.muted,
          letterSpacing: 1.5,
          marginBottom: 8,
        }}
      >
        ◆ {title.toUpperCase()}
      </div>
      <div style={{ fontSize: 14, lineHeight: 1.65, color: palette.text }}>{children}</div>
    </div>
  )
}

function liStyle(palette: Palette): React.CSSProperties {
  return {
    margin: '8px 0',
    paddingLeft: 20,
    color: palette.text,
  }
}

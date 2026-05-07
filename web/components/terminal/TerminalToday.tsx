'use client'

import { useMemo, useState } from 'react'
import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import { useUpcomingPicks, type RawPick } from '@/lib/use-upcoming-picks'
import { useEspnSchedule, findEspnGame } from '@/lib/use-espn-schedule'
import { GameCard } from './GameCard'
import { DetailPanel } from './DetailPanel'
import { SportFilter } from './SportFilter'
import { SortFilter, americanToDecimal, type SortMode } from './SortFilter'
import { rawPickToGameCard, flattenUpcoming } from '@/lib/pick-adapter'

const MODEL_OPTIONS = [
  { label: 'V1', value: 'logreg' },
  { label: 'V2', value: 'logreg_v2' },
]

interface Props {
  palette: Palette
}

interface SelectedPick {
  raw: RawPick
  sport: string
  gameTime: string
}

interface FlatItem {
  sport: string
  raw: RawPick
  bucket: 'today' | 'tomorrow'
}

function sortItems(items: FlatItem[], mode: SortMode): FlatItem[] {
  const scored = items.map((item) => {
    const ev = item.raw.ev
    const conf = item.raw.confidence
    const dec = americanToDecimal(item.raw.bet_line)
    let primary: number
    let hasValue = true
    switch (mode) {
      case 'EDGE':
        primary = ev != null && Number.isFinite(ev) ? -ev : Infinity
        hasValue = ev != null && Number.isFinite(ev)
        break
      case 'CONFIDENCE':
        primary = conf != null && Number.isFinite(conf) ? -conf : Infinity
        hasValue = conf != null && Number.isFinite(conf)
        break
      case 'LONGSHOT':
        primary = dec != null ? -dec : Infinity
        hasValue = dec != null
        break
      case 'FAVORITE':
        primary = dec != null ? dec : Infinity
        hasValue = dec != null
        break
    }
    return { item, primary, hasValue }
  })
  scored.sort((a, b) => {
    if (a.hasValue !== b.hasValue) return a.hasValue ? -1 : 1
    return a.primary - b.primary
  })
  return scored.map((s) => s.item)
}

function getAbbrs(raw: RawPick): { awayAbbr: string; homeAbbr: string } {
  return {
    awayAbbr: raw.away_abbr || (raw.away_team ?? '?').slice(0, 3).toUpperCase(),
    homeAbbr: raw.home_abbr || (raw.home_team ?? '?').slice(0, 3).toUpperCase(),
  }
}

export function TerminalToday({ palette }: Props) {
  const today = new Date().toISOString().slice(0, 10)
  const [model, setModel] = useState('logreg_v2')

  // Both models are fetched in parallel on mount so switching is instant.
  const { status: statusV1, data: dataV1, error: errorV1 } = useUpcomingPicks(today, 'logreg')
  const { status: statusV2, data: dataV2, error: errorV2 } = useUpcomingPicks(today, 'logreg_v2')
  const status = model === 'logreg_v2' ? statusV2 : statusV1
  const data   = model === 'logreg_v2' ? dataV2   : dataV1
  const error  = model === 'logreg_v2' ? errorV2  : errorV1

  const [selected, setSelected] = useState<SelectedPick | null>(null)
  const [filter, setFilter] = useState<string>('ALL')
  const [sort, setSort] = useState<SortMode>('EDGE')
  const [picksOnly, setPicksOnly] = useState(true)

  const all = useMemo(() => (data ? flattenUpcoming(data.sports) : []), [data])
  const sportsAvail = useMemo(() => {
    const set = new Set<string>()
    for (const item of all) set.add(item.sport.toUpperCase())
    return Array.from(set).sort()
  }, [all])

  // Fetch ESPN schedule for today's sports (for game times + started-game filtering)
  const espnSchedule = useEspnSchedule(today, sportsAvail)

  const filtered = useMemo(() => {
    let base = filter === 'ALL' ? all : all.filter((x) => x.sport.toUpperCase() === filter)
    if (picksOnly) base = base.filter((x) => x.raw.pick && x.raw.pick !== 'No Pick' && x.raw.ev != null && x.raw.ev >= 0)
    return sortItems(base, sort)
  }, [all, filter, sort, picksOnly])

  // Remove today's games that have already started
  const displayItems = useMemo(() => {
    return filtered.filter((item) => {
      if (item.bucket !== 'today') return true
      const { awayAbbr, homeAbbr } = getAbbrs(item.raw)
      const match = findEspnGame(espnSchedule[item.sport] ?? [], awayAbbr, homeAbbr)
      return !(match?.started ?? false)
    })
  }, [filtered, espnSchedule])

  const dateLabel = new Date().toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
    weekday: 'long',
  })

  return (
    <div
      style={{
        padding: '32px',
        display: 'grid',
        gridTemplateColumns: selected ? '1fr 420px' : '1fr',
        gap: 24,
        maxWidth: 1376,
        margin: '0 auto',
      }}
    >
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
            marginBottom: 24,
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 11,
                color: palette.muted,
                letterSpacing: 1.5,
                marginBottom: 6,
              }}
            >
              {dateLabel.toUpperCase()}
            </div>
            <h2 style={{ fontSize: 36, fontWeight: 500, margin: 0, letterSpacing: -1 }}>
              Today&apos;s Board
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: 4, fontFamily: FONT_MONO, fontSize: 11 }}>
              {MODEL_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setModel(opt.value)}
                  style={{
                    padding: '6px 10px',
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    letterSpacing: 0.5,
                    cursor: 'pointer',
                    background: model === opt.value ? palette.blue : 'transparent',
                    color: model === opt.value ? palette.bg : palette.muted,
                    border: `1px solid ${model === opt.value ? palette.blue : palette.border}`,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div style={{ width: 1, height: 20, background: palette.border, margin: '0 4px' }} />
            <button
              onClick={() => setPicksOnly(!picksOnly)}
              style={{
                padding: '6px 12px',
                fontFamily: FONT_MONO,
                fontSize: 11,
                letterSpacing: 0.5,
                cursor: 'pointer',
                background: picksOnly ? palette.accent : 'transparent',
                color: picksOnly ? palette.bg : palette.muted,
                border: `1px solid ${picksOnly ? palette.accent : palette.border}`,
              }}
            >
              SUGGESTED BETS
            </button>
            <SortFilter palette={palette} value={sort} onChange={setSort} />
            <SportFilter
              palette={palette}
              options={['ALL', ...sportsAvail]}
              value={filter}
              onChange={setFilter}
            />
          </div>
        </div>

        {status === 'loading' && (
          <div
            style={{
              padding: 48,
              textAlign: 'center',
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.muted,
              letterSpacing: 1,
            }}
          >
            FETCHING PICKS…
          </div>
        )}
        {status === 'error' && (
          <div
            style={{
              padding: 24,
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: palette.danger,
              border: `1px solid ${palette.border}`,
              background: palette.surface,
            }}
          >
            ERROR: {error}
          </div>
        )}
        {status === 'ready' && displayItems.length === 0 && (
          <div
            style={{
              padding: 48,
              textAlign: 'center',
              fontFamily: FONT_MONO,
              fontSize: 12,
              color: palette.muted,
            }}
          >
            {filtered.length > 0
              ? "All of today's games have already started."
              : picksOnly
              ? "Our model hasn't found any profitable games today."
              : 'NO GAMES FOR THIS FILTER.'}
          </div>
        )}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: selected ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)',
            gap: 12,
          }}
        >
          {displayItems.map((item, i) => {
            const { awayAbbr, homeAbbr } = getAbbrs(item.raw)
            const espnMatch = findEspnGame(espnSchedule[item.sport] ?? [], awayAbbr, homeAbbr)
            const gameTime =
              espnMatch?.startTimeLocal ?? (item.bucket === 'tomorrow' ? 'TOMORROW' : 'TODAY')
            const card = rawPickToGameCard(item.raw, item.sport, gameTime)
            return (
              <GameCard
                key={`${item.sport}-${item.raw.game_index}-${i}`}
                g={card}
                palette={palette}
                onClick={() => setSelected({ raw: item.raw, sport: item.sport, gameTime })}
              />
            )
          })}
        </div>
      </div>

      {selected && (
        <DetailPanel
          palette={palette}
          pick={selected.raw}
          sport={selected.sport}
          gameTime={selected.gameTime}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}

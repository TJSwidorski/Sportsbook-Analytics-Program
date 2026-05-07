'use client'

import { useCallback } from 'react'
import { useCachedFetch } from './cached-fetch'

export interface EspnGame {
  awayAbbr: string
  homeAbbr: string
  startTimeISO: string
  startTimeLocal: string
  started: boolean
  completed: boolean
}

export type EspnScheduleMap = Record<string, EspnGame[]>

const ESPN_PATHS: Record<string, string> = {
  nba: 'basketball/nba',
  nhl: 'hockey/nhl',
  mlb: 'baseball/mlb',
  nfl: 'football/nfl',
  wnba: 'basketball/wnba',
  mls: 'soccer/usa.1',
  cfl: 'football/cfl',
}

// SBR abbr -> ESPN abbr overrides; fill in as mismatches are discovered
const SBR_TO_ESPN: Record<string, string> = {}

function normalizeAbbr(abbr: string): string {
  const up = abbr.toUpperCase()
  return SBR_TO_ESPN[up] ?? up
}

interface EspnEvent {
  date: string
  status: { type: { state: string; completed: boolean } }
  competitions: Array<{
    competitors: Array<{ homeAway: string; team: { abbreviation: string } }>
  }>
}

async function fetchSportGames(sport: string, date: string): Promise<EspnGame[]> {
  const path = ESPN_PATHS[sport]
  if (!path) return []
  const dateStr = date.replace(/-/g, '')
  try {
    const res = await fetch(
      `https://site.api.espn.com/apis/site/v2/sports/${path}/scoreboard?dates=${dateStr}`,
    )
    if (!res.ok) return []
    const data: { events?: EspnEvent[] } = await res.json()
    if (!data.events) return []
    return data.events.map((ev) => {
      const comp = ev.competitions[0]
      const away = comp?.competitors.find((c) => c.homeAway === 'away')
      const home = comp?.competitors.find((c) => c.homeAway === 'home')
      const d = new Date(ev.date)
      return {
        awayAbbr: away?.team.abbreviation ?? '',
        homeAbbr: home?.team.abbreviation ?? '',
        startTimeISO: ev.date,
        startTimeLocal: d.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true,
        }),
        started: ev.status.type.state !== 'pre',
        completed: ev.status.type.completed,
      }
    })
  } catch {
    return []
  }
}

export function useEspnSchedule(date: string, sports: string[]): EspnScheduleMap {
  const sportsKey = sports
    .map((s) => s.toLowerCase())
    .filter((s) => s in ESPN_PATHS)
    .sort()
    .join(',')

  const cacheKey = `espn:${date}:${sportsKey}`

  const fetcher = useCallback(async (): Promise<EspnScheduleMap> => {
    const result: EspnScheduleMap = {}
    if (!sportsKey) return result
    await Promise.all(
      sportsKey.split(',').map(async (sport) => {
        result[sport] = await fetchSportGames(sport, date)
      }),
    )
    return result
  }, [date, sportsKey])

  const { data } = useCachedFetch<EspnScheduleMap>(cacheKey, fetcher)
  return data ?? {}
}

export function findEspnGame(
  games: EspnGame[],
  awayAbbr: string,
  homeAbbr: string,
): EspnGame | undefined {
  const na = normalizeAbbr(awayAbbr)
  const nh = normalizeAbbr(homeAbbr)
  return games.find(
    (g) => normalizeAbbr(g.awayAbbr) === na && normalizeAbbr(g.homeAbbr) === nh,
  )
}

'use client'

import { useCallback } from 'react'
import { jsonFetch, useCachedFetch } from './cached-fetch'

export interface RawPick {
  game_index: number
  pick: string
  confidence: number | null
  away_prob: number | null
  home_prob: number | null
  away_lines: string[]
  home_lines: string[]
  away_team?: string
  home_team?: string
  away_abbr?: string
  home_abbr?: string
  sportsbooks?: string[]
  ev?: number | null
  unit_size?: number
  bet_line?: string | null
  model?: string
}

export interface SportSlate {
  today: RawPick[]
  tomorrow: RawPick[]
}

export interface UpcomingResponse {
  date: string
  tomorrow_date: string
  sports: Record<string, SportSlate>
  error?: string
}

export type Status = 'loading' | 'ready' | 'error'

interface UseUpcomingResult {
  status: Status
  data: UpcomingResponse | null
  error: string | null
  refetch: () => void
}

export function useUpcomingPicks(date: string, model = 'logreg_v2'): UseUpcomingResult {
  const fetcher = useCallback(
    () => jsonFetch<UpcomingResponse>(`/api/picks/upcoming?date=${date}&model=${model}`),
    [date, model],
  )
  const { status, data, error, refetch } = useCachedFetch<UpcomingResponse>(
    `upcoming:${date}:${model}`,
    fetcher,
  )
  const narrowed: Status = status === 'empty' ? 'ready' : status
  return { status: narrowed, data, error, refetch }
}

export interface UpcomingStats {
  totalPicks: number
  sportsLive: number
  avgConfidence: number | null
}

export function summarizeUpcoming(data: UpcomingResponse | null): UpcomingStats {
  if (!data) return { totalPicks: 0, sportsLive: 0, avgConfidence: null }

  const allPicks: RawPick[] = []
  let sportsLive = 0
  for (const slate of Object.values(data.sports)) {
    const combined = [...slate.today, ...slate.tomorrow]
    if (combined.length > 0) sportsLive += 1
    allPicks.push(...combined)
  }
  if (allPicks.length === 0) {
    return { totalPicks: 0, sportsLive, avgConfidence: null }
  }
  const confidences = allPicks
    .map((p) => p.confidence)
    .filter((c): c is number => c != null && Number.isFinite(c))
  const avg = confidences.length
    ? confidences.reduce((s, v) => s + v, 0) / confidences.length
    : null
  return { totalPicks: allPicks.length, sportsLive, avgConfidence: avg }
}

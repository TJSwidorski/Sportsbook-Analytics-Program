'use client'

import { useCallback } from 'react'
import { jsonFetch, useCachedFetch } from './cached-fetch'

export interface RecentPick {
  date: string
  sport: string
  matchup: string
  pick: string
  bet_line: string | null
  result: string | null
  actual: string | null
  units: number | null
  kelly_units: number | null
  unit_size: number | null
  ev: number | null
}

interface RecentPicksResponse {
  picks: RecentPick[]
  error?: string
}

export type Status = 'loading' | 'ready' | 'error'

export function useRecentPicks(limit = 50) {
  const fetcher = useCallback(
    () => jsonFetch<RecentPicksResponse>(`/api/history/recent-picks?limit=${limit}`),
    [limit],
  )
  const { status, data, error } = useCachedFetch<RecentPicksResponse>(
    `recent:${limit}`,
    fetcher,
  )
  const narrowed: Status = status === 'empty' ? 'ready' : status
  return { status: narrowed, picks: data?.picks ?? [], error }
}

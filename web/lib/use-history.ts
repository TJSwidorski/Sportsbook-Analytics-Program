'use client'

import { useCallback } from 'react'
import { jsonFetch, useCachedFetch } from './cached-fetch'

export interface HistorySportRow {
  sport: string
  season_year: number
  model: string
  start_date: string
  end_date: string
  total_games: number
  games_picked: number
  correct_picks: number
  win_rate: number | null
  flat_units: number
  kelly_units: number
  roi_flat: number | null
  roi_kelly: number | null
  max_drawdown: number | null
  computed_at: string
}

export interface HistoryTotals {
  games_picked: number
  correct_picks: number
  win_rate: number | null
  flat_units: number
  kelly_units: number
  roi_flat: number | null
  roi_kelly: number | null
  max_drawdown: number | null
  earliest_year: number | null
}

export interface HistoryResponse {
  model: string
  sports: HistorySportRow[]
  totals: HistoryTotals | null
  error?: string
}

export type Status = 'loading' | 'ready' | 'error' | 'empty'

export function useHistory(model = 'logreg') {
  const fetcher = useCallback(
    () => jsonFetch<HistoryResponse>(`/api/history?model=${model}`, { acceptStatus404: true }),
    [model],
  )
  const { status, data, error } = useCachedFetch<HistoryResponse>(
    `history:${model}`,
    fetcher,
    { acceptStatus404: true },
  )
  return { status: status as Status, data, error }
}

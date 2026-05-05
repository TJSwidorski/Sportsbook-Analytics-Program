'use client'

import { useCallback } from 'react'
import { jsonFetch, useCachedFetch } from './cached-fetch'

export interface PerformancePoint {
  day: string
  units: number
  kelly_units: number
  cum_units: number
  cum_kelly_units: number
}

export interface RollingSportRow {
  sport: string
  end_date: string
  window_days: number
  start_date: string
  total_games: number
  games_picked: number
  correct_picks: number
  win_rate: number | null
  flat_units: number
  kelly_units: number
  max_drawdown: number
  daily_units: PerformancePoint[]
}

export interface RollingTotals {
  games_picked: number
  correct_picks: number
  win_rate: number | null
  flat_units: number
  kelly_units: number
  max_drawdown: number
}

interface RollingResponse {
  days: number
  model?: string
  series: PerformancePoint[]
  sports: RollingSportRow[]
  totals: RollingTotals | null
  error?: string
}

export type Status = 'loading' | 'ready' | 'error'

/**
 * Rolling N-day backtest results for every in-season sport. Backed by the
 * server-side `rolling_backtest_cache` table which is refreshed daily by the
 * prefetch thread. The first hit on a fresh DB triggers a synchronous compute.
 */
export function usePerformance(days = 30, model = 'logreg_v2') {
  const fetcher = useCallback(
    () => jsonFetch<RollingResponse>(`/api/history/rolling?days=${days}&model=${model}`),
    [days, model],
  )
  const { status, data, error } = useCachedFetch<RollingResponse>(
    `rolling:${days}:${model}`,
    fetcher,
  )
  const narrowed: Status = status === 'empty' ? 'ready' : status
  return {
    status: narrowed,
    series: data?.series ?? [],
    sports: data?.sports ?? [],
    totals: data?.totals ?? null,
    error,
  }
}

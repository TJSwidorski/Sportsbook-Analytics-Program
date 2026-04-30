'use client'

import { useCallback, useState } from 'react'

export interface BacktestGameLog {
  game_index: number
  date_or_week: string
  pick: string
  actual: string
  correct: boolean | null
  units: number
  kelly_units: number
  bet_line: string | null
  unit_size: number
  ev: number | null
  away_lines: string[]
  home_lines: string[]
}

export interface BacktestResult {
  sport: string
  model: string
  start: string
  end: string
  total_games: number
  games_picked: number
  correct_picks: number
  accuracy: number | null
  total_units: number
  flat_units: number
  kelly_units: number
  max_drawdown: number
  game_log: BacktestGameLog[]
  error?: string
}

export type Status = 'idle' | 'running' | 'ready' | 'error'

export interface BacktestRequest {
  sport: string
  start: string
  end: string
  model?: string
}

export function useBacktest() {
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (req: BacktestRequest) => {
    setStatus('running')
    setError(null)
    try {
      const res = await fetch('/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      })
      const text = await res.text()
      let parsed: BacktestResult
      try {
        parsed = JSON.parse(text) as BacktestResult
      } catch {
        throw new Error(`Non-JSON response (HTTP ${res.status})`)
      }
      if (!res.ok || parsed.error) {
        throw new Error(parsed.error ?? `HTTP ${res.status}`)
      }
      setResult(parsed)
      setStatus('ready')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setStatus('error')
    }
  }, [])

  return { status, result, error, run }
}

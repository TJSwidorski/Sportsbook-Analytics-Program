'use client'

import { useEffect, useRef, useState } from 'react'

// In production (static export on Cloudflare) the browser calls the Flask API
// directly.  Set NEXT_PUBLIC_API_BASE_URL=https://api.axiompicks.com in the
// Cloudflare Pages environment variables.
// For local dev set it to http://localhost:5000 in web/.env.local.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''

export type CachedStatus = 'loading' | 'ready' | 'error' | 'empty'

export interface CachedResult<T> {
  status: CachedStatus
  data: T | null
  error: string | null
  refetch: () => void
}

export interface CachedFetchOptions {
  // Map a 404 onto status='empty' instead of 'error', preserving the body.
  // /api/history uses this to surface "run backtest_history.py" guidance.
  acceptStatus404?: boolean
}

interface InternalEntry<T> {
  data: T
  ts: number
}

const memCache = new Map<string, InternalEntry<unknown>>()
const inflight = new Map<string, Promise<unknown>>()

function readSession<T>(key: string): T | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(`axiom:${key}`)
    if (!raw) return null
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function writeSession<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(`axiom:${key}`, JSON.stringify(value))
  } catch {
    // quota / SSR edge case — silently ignore
  }
}

class EmptyResponseError extends Error {
  payload: unknown
  constructor(payload: unknown) {
    super('empty')
    this.name = 'EmptyResponseError'
    this.payload = payload
  }
}

export async function jsonFetch<T>(url: string, opts: CachedFetchOptions = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`)
  const text = await res.text()
  let parsed: unknown
  try {
    parsed = text ? JSON.parse(text) : null
  } catch {
    throw new Error(`Non-JSON response (HTTP ${res.status})`)
  }
  if (res.status === 404 && opts.acceptStatus404) {
    throw new EmptyResponseError(parsed)
  }
  if (!res.ok) {
    const errMessage =
      parsed && typeof parsed === 'object' && parsed !== null && 'error' in parsed
        ? String((parsed as { error?: unknown }).error)
        : `HTTP ${res.status}`
    throw new Error(errMessage)
  }
  return parsed as T
}

/**
 * Stale-while-revalidate hook.
 *
 * - Module cache → instant data on subsequent mounts within one SPA session.
 * - sessionStorage → instant data after F5 in the same browser tab.
 * - Inflight Map → two simultaneous mounts share one network request.
 *
 * `fetcher` MUST be stable per `key` — wrap with useCallback or define
 * outside the component if it captures props/state.
 */
export function useCachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: CachedFetchOptions = {},
): CachedResult<T> {
  const [data, setData] = useState<T | null>(() => {
    const mem = memCache.get(key) as InternalEntry<T> | undefined
    if (mem) return mem.data
    const session = readSession<T>(key)
    if (session) {
      memCache.set(key, { data: session, ts: Date.now() })
      return session
    }
    return null
  })
  const [status, setStatus] = useState<CachedStatus>(data != null ? 'ready' : 'loading')
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      let promise = inflight.get(key) as Promise<T> | undefined
      if (!promise) {
        promise = fetcher()
        inflight.set(key, promise as Promise<unknown>)
        promise.finally(() => {
          if (inflight.get(key) === promise) inflight.delete(key)
        })
      }

      try {
        const result = await promise
        if (cancelled) return
        memCache.set(key, { data: result, ts: Date.now() })
        writeSession(key, result)
        setData(result)
        setStatus('ready')
        setError(null)
      } catch (e: unknown) {
        if (cancelled) return
        if (e instanceof EmptyResponseError && options.acceptStatus404) {
          setData(e.payload as T)
          setStatus('empty')
          const msg =
            e.payload && typeof e.payload === 'object' && e.payload !== null && 'error' in e.payload
              ? String((e.payload as { error?: unknown }).error)
              : null
          setError(msg)
          return
        }
        setStatus(memCache.has(key) ? 'ready' : 'error')
        setError(e instanceof Error ? e.message : 'Unknown error')
      }
    }

    void run()

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick])

  return {
    status,
    data,
    error,
    refetch: () => {
      memCache.delete(key)
      setTick((t) => t + 1)
    },
  }
}

export function clearCachedKey(key: string): void {
  memCache.delete(key)
  if (typeof window !== 'undefined') {
    try {
      window.sessionStorage.removeItem(`axiom:${key}`)
    } catch {
      // ignore
    }
  }
}

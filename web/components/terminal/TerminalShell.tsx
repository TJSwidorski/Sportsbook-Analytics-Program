'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Sun, Moon } from 'lucide-react'
import { getPalette, FONT_MONO } from '@/lib/palette'
import { MeshBg } from './MeshBg'
import { TerminalHome } from './TerminalHome'
import { TerminalToday } from './TerminalToday'
import { TerminalHistory } from './TerminalHistory'
import { TerminalBacktest } from './TerminalBacktest'
import { TerminalAbout } from './TerminalAbout'
import { useHistory } from '@/lib/use-history'
import { usePerformance } from '@/lib/use-performance'
import { useUpcomingPicks } from '@/lib/use-upcoming-picks'

type TabId = 'home' | 'today' | 'history' | 'backtest' | 'about'

const TABS: { id: TabId; label: string }[] = [
  { id: 'home', label: 'HOME' },
  { id: 'today', label: 'TODAY' },
  { id: 'history', label: 'HISTORY' },
  { id: 'backtest', label: 'BACKTEST' },
  { id: 'about', label: 'ABOUT' },
]

const TICKER_REFRESH_MS = 5 * 60 * 1000   // match backend PICKS_REFRESH_INTERVAL

function TickerStrip() {
  const today = new Date().toISOString().slice(0, 10)
  const { data: history } = useHistory()
  const { series } = usePerformance(30)
  const { data: upcoming, refetch: refetchUpcoming } = useUpcomingPicks(today)

  // Re-fetch in sync with the server's 5-minute picks-refresh cycle so the
  // UPDATED timestamp and open-picks count stay current throughout the day.
  useEffect(() => {
    const id = setInterval(refetchUpcoming, TICKER_REFRESH_MS)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const palette = getPalette(typeof document !== 'undefined' && document.documentElement.classList.contains('dark'))

  const totals = history?.totals ?? null
  const winRate = totals?.win_rate != null ? `${(totals.win_rate * 100).toFixed(1)}%` : '—'
  const last30 = series.length > 0 ? series[series.length - 1].cum_units : 0
  const last30Label = `${last30 >= 0 ? '+' : ''}${last30.toFixed(1)}`
  const yearTotal = totals?.flat_units ?? 0
  const ytd = `${yearTotal >= 0 ? '+' : ''}${yearTotal.toFixed(1)}`
  const ytdRoi =
    totals?.roi_flat != null
      ? `${totals.roi_flat * 100 >= 0 ? '+' : ''}${(totals.roi_flat * 100).toFixed(1)}%`
      : '—'
  const openPicks = upcoming
    ? Object.values(upcoming.sports).reduce((s, x) => s + x.today.length + x.tomorrow.length, 0)
    : 0

  // Show the server-stamped scrape time so users know how fresh the picks are.
  const updated = upcoming?.cached_at
    ? new Date(upcoming.cached_at * 1000).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })
    : new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })

  return (
    <div
      style={{
        height: 28,
        borderBottom: `1px solid ${palette.border}`,
        background: palette.surface,
        fontFamily: FONT_MONO,
        fontSize: 11,
        display: 'flex',
        alignItems: 'center',
        gap: 32,
        padding: '0 16px',
        color: palette.muted,
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        position: 'relative',
        zIndex: 5,
      }}
    >
      <span style={{ color: palette.accent, fontWeight: 600 }}>● LIVE</span>
      <span>
        WIN_RATE <span style={{ color: palette.accent }}>{winRate}</span>
      </span>
      <span>
        30D_UNITS <span style={{ color: palette.accent }}>{last30Label}</span>
      </span>
      <span>
        YTD_UNITS <span style={{ color: palette.accent }}>{ytd}</span>
      </span>
      <span>
        ROI <span style={{ color: palette.accent }}>{ytdRoi}</span>
      </span>
      <span>
        OPEN_PICKS <span style={{ color: palette.blue }}>{openPicks}</span>
      </span>
      <span>
        MODEL <span style={{ color: palette.blue }}>logreg_v2</span>
      </span>
      <span>
        UPDATED <span style={{ color: palette.text }}>{updated}</span>
      </span>
    </div>
  )
}

export function TerminalShell() {
  const [tab, setTab] = useState<TabId>('home')
  const [dark, setDark] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const palette = useMemo(() => getPalette(dark), [dark])

  useEffect(() => {
    if (typeof document === 'undefined') return
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <div
      style={{
        background: palette.bg,
        color: palette.text,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        fontSize: 13,
        minHeight: '100vh',
      }}
    >
      <TickerStrip />

      <header
        style={{
          height: 56,
          borderBottom: `1px solid ${palette.border}`,
          background: palette.surface,
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          gap: 32,
          position: 'relative',
          zIndex: 5,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M2 18 L11 4 L20 18" stroke={palette.text} strokeWidth="1.5" />
            <path d="M6 13 L16 13" stroke={palette.text} strokeWidth="1.5" />
            <circle cx="11" cy="4" r="1.6" fill={palette.accent} />
            <circle cx="2" cy="18" r="1.4" fill={palette.blue} />
            <circle cx="20" cy="18" r="1.4" fill={palette.blue} />
          </svg>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: 1,
            }}
          >
            AXIOM<span style={{ color: palette.muted, fontWeight: 400 }}> PICKS</span>
          </div>
        </div>
        <nav style={{ display: 'flex', gap: 4, fontFamily: FONT_MONO, fontSize: 12 }}>
          {TABS.map((t) => {
            const active = tab === t.id
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: '6px 12px',
                  background: active ? palette.surface2 : 'transparent',
                  border: active
                    ? `1px solid ${palette.border2}`
                    : '1px solid transparent',
                  color: active ? palette.text : palette.muted,
                  cursor: 'pointer',
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  letterSpacing: 0.5,
                }}
              >
                {t.label}
              </button>
            )
          })}
        </nav>
        <div
          style={{
            marginLeft: 'auto',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <button
            onClick={() => setDark(!dark)}
            aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{
              width: 32,
              height: 32,
              background: palette.surface2,
              border: `1px solid ${palette.border2}`,
              borderRadius: 0,
              cursor: 'pointer',
              padding: 0,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: palette.text,
            }}
          >
            {dark ? <Sun size={16} strokeWidth={1.6} /> : <Moon size={16} strokeWidth={1.6} />}
          </button>
        </div>
      </header>

      <div ref={scrollRef} style={{ flex: 1, position: 'relative' }}>
        <MeshBg
          dark={dark}
          accentA={palette.accent}
          accentB={palette.blue}
          scrollEl={scrollRef}
        />
        <div style={{ position: 'relative', zIndex: 1 }}>
          {tab === 'home' && <TerminalHome palette={palette} />}
          {tab === 'today' && <TerminalToday palette={palette} />}
          {tab === 'history' && <TerminalHistory palette={palette} />}
          {tab === 'backtest' && <TerminalBacktest palette={palette} />}
          {tab === 'about' && <TerminalAbout palette={palette} />}
        </div>
      </div>

      <footer
        style={{
          borderTop: `1px solid ${palette.border}`,
          background: palette.surface,
          fontFamily: FONT_MONO,
          fontSize: 10,
          color: palette.muted,
          textAlign: 'center',
          padding: '8px 16px',
          lineHeight: 1.6,
          position: 'relative',
          zIndex: 5,
        }}
      >
        FOR INFORMATIONAL &amp; ENTERTAINMENT PURPOSES ONLY · NOT FINANCIAL ADVICE · 21+ · GAMBLING MAY BE ILLEGAL IN YOUR JURISDICTION
        <span style={{ marginLeft: 16, opacity: 0.6 }}>
          PROBLEM GAMBLING HELPLINE: 1-800-GAMBLER
        </span>
      </footer>
    </div>
  )
}

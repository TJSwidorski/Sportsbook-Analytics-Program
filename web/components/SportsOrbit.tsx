'use client'

// Adapted from home_screen.txt (stack-feature-section) — orbiting sports badges
// instead of tech icons.

import { cn } from '@/lib/utils'

const SPORTS = [
  { key: 'NBA',   color: '#E03131', bg: '#2A1515' },
  { key: 'NFL',   color: '#4A90D9', bg: '#121D2A' },
  { key: 'NHL',   color: '#7B68EE', bg: '#16142A' },
  { key: 'MLB',   color: '#FF6B35', bg: '#241910' },
  { key: 'MLS',   color: '#00B2A9', bg: '#0A1E1D' },
  { key: 'NCAAF', color: '#E97700', bg: '#201500' },
  { key: 'NCAAB', color: '#3D8BFF', bg: '#101D30' },
  { key: 'WNBA',  color: '#FF6900', bg: '#201500' },
  { key: 'CFL',   color: '#FF4D6D', bg: '#251020' },
]

function SportBadge({ sport, style }: { sport: typeof SPORTS[0]; style?: React.CSSProperties }) {
  return (
    <div
      className="absolute flex items-center justify-center rounded-full"
      style={{
        left: (style as { left?: string })?.left,
        top: (style as { top?: string })?.top,
        transform: 'translate(-50%, -50%)',
        ...style,
      }}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center shadow-lg border"
        style={{
          backgroundColor: sport.bg,
          borderColor: sport.color + '40',
          boxShadow: `0 0 12px ${sport.color}30`,
        }}
      >
        <span
          className="text-[9px] font-mono-data font-bold"
          style={{ color: sport.color }}
        >
          {sport.key}
        </span>
      </div>
    </div>
  )
}

function Orbit({
  sports,
  size,
  duration,
  reverse = false,
}: {
  sports: typeof SPORTS
  size: number
  duration: number
  reverse?: boolean
}) {
  const angleStep = (2 * Math.PI) / sports.length
  return (
    <div
      className={cn('absolute rounded-full border border-dashed border-border-subtle/30')}
      style={{
        width: size,
        height: size,
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        animation: `spin ${duration}s linear infinite${reverse ? ' reverse' : ''}`,
      }}
    >
      {sports.map((sport, i) => {
        const angle = i * angleStep
        const x = 50 + 50 * Math.cos(angle)
        const y = 50 + 50 * Math.sin(angle)
        return (
          <div
            key={sport.key}
            style={{
              position: 'absolute',
              left: `${x}%`,
              top: `${y}%`,
              transform: 'translate(-50%, -50%)',
              // Counter-rotate so badge text stays upright
              animation: `spin ${duration}s linear infinite${!reverse ? ' reverse' : ''}`,
            }}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center shadow-lg border"
              style={{
                backgroundColor: sport.bg,
                borderColor: sport.color + '40',
                boxShadow: `0 0 12px ${sport.color}30`,
              }}
            >
              <span className="text-[9px] font-mono-data font-bold" style={{ color: sport.color }}>
                {sport.key}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function SportsOrbit() {
  const inner = SPORTS.slice(0, 3)
  const mid   = SPORTS.slice(3, 6)
  const outer = SPORTS.slice(6, 9)

  return (
    <div className="relative w-full h-full flex items-center justify-start overflow-hidden">
      <div
        className="relative flex items-center justify-center"
        style={{ width: '36rem', height: '36rem', transform: 'translateX(30%)' }}
      >
        {/* Center hub */}
        <div className="relative z-10 w-24 h-24 rounded-full glass flex flex-col items-center justify-center glow-mint">
          <div className="w-2 h-2 rounded-full bg-mint mb-1 animate-pulse-soft" />
          <span className="text-[9px] font-mono-data text-txt-muted uppercase tracking-widest">Today</span>
          <span className="text-xs font-display font-semibold text-mint">Picks</span>
        </div>

        {/* 3 concentric orbits */}
        <Orbit sports={inner} size={200} duration={18} />
        <Orbit sports={mid}   size={310} duration={28} reverse />
        <Orbit sports={outer} size={420} duration={40} />
      </div>

      {/* Right-side fade mask */}
      <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-bg-primary to-transparent pointer-events-none" />
      <div className="absolute top-0 bottom-0 left-0 w-8 bg-gradient-to-r from-bg-primary to-transparent pointer-events-none" />
    </div>
  )
}

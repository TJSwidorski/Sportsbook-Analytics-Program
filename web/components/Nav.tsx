'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

export function Nav() {
  const pathname = usePathname()

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <div className="mx-auto max-w-7xl px-6 py-4">
        <div className="flex items-center justify-between glass rounded-2xl px-6 py-3">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-mint rounded-md opacity-20 group-hover:opacity-30 transition-opacity" />
              <div className="absolute inset-1 bg-mint rounded-sm opacity-80" />
            </div>
            <span className="font-display text-xl font-semibold tracking-tight text-txt-primary">
              AXIOM
            </span>
            <span className="hidden sm:block text-xs font-mono-data text-txt-muted uppercase tracking-widest">
              Picks
            </span>
          </Link>

          {/* Nav links */}
          <nav className="flex items-center gap-1">
            <Link
              href="/"
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                pathname === '/'
                  ? 'bg-bg-elevated text-mint border border-mint/20'
                  : 'text-txt-secondary hover:text-txt-primary hover:bg-bg-elevated/60',
              )}
            >
              Today&apos;s Picks
            </Link>
            <Link
              href="/backtest"
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                pathname === '/backtest'
                  ? 'bg-bg-elevated text-mint border border-mint/20'
                  : 'text-txt-secondary hover:text-txt-primary hover:bg-bg-elevated/60',
              )}
            >
              Backtest
            </Link>
          </nav>

          {/* Status indicator */}
          <div className="hidden sm:flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-mint animate-pulse-soft" />
            <span className="text-xs font-mono-data text-txt-muted">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  )
}

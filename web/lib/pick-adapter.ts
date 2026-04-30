import type { RawPick } from './use-upcoming-picks'
import type { GameCardData } from '@/components/terminal/GameCard'

/**
 * Bin a raw model probability into a humanized confidence label so a
 * non-technical reader sees "HIGH" alongside the percent rather than just
 * "67%" with no anchor for what the number means.
 */
export function confidenceTier(conf: number): 'HIGH' | 'MODERATE' | 'LEAN' | null {
  if (!Number.isFinite(conf)) return null
  if (conf >= 65) return 'HIGH'
  if (conf >= 55) return 'MODERATE'
  if (conf >= 50) return 'LEAN'
  return null
}

export function rawPickToGameCard(p: RawPick, sport: string, time = 'TBD'): GameCardData {
  const awayAbbr = p.away_abbr || (p.away_team ?? '?').slice(0, 3).toUpperCase()
  const homeAbbr = p.home_abbr || (p.home_team ?? '?').slice(0, 3).toUpperCase()
  const teamLabel =
    p.pick === 'Away' ? awayAbbr : p.pick === 'Home' ? homeAbbr : p.pick
  const isNoBet = p.pick === 'No Pick' || !p.pick || (p.ev != null && p.ev < 0)
  const pickLabel = isNoBet
    ? 'NO BET'
    : p.bet_line
    ? `${teamLabel} ${p.bet_line}`
    : teamLabel
  const conf = p.confidence != null && Number.isFinite(p.confidence) ? Math.round(p.confidence * 100) : 0
  const ev = p.ev != null && Number.isFinite(p.ev) ? p.ev * 100 : null
  const edge = ev == null ? '—' : `${ev >= 0 ? '+' : ''}${ev.toFixed(1)}%`
  const unit = p.unit_size != null && Number.isFinite(p.unit_size) ? p.unit_size * 100 : 0
  const units = `${unit.toFixed(1)}u`
  return {
    sport: sport.toLowerCase(),
    league: sport.toUpperCase(),
    away: p.away_team ?? awayAbbr,
    home: p.home_team ?? homeAbbr,
    awayAbbr,
    homeAbbr,
    time,
    pick: pickLabel,
    confidence: conf,
    confidenceTier: confidenceTier(conf),
    edge,
    edgeValue: ev,
    units,
    isNoBet,
  }
}

export function flattenUpcoming(
  sports: Record<string, { today: RawPick[]; tomorrow: RawPick[] }>,
): { sport: string; raw: RawPick; bucket: 'today' | 'tomorrow' }[] {
  const out: { sport: string; raw: RawPick; bucket: 'today' | 'tomorrow' }[] = []
  for (const [sport, slate] of Object.entries(sports)) {
    for (const p of slate.today) out.push({ sport, raw: p, bucket: 'today' })
    for (const p of slate.tomorrow) out.push({ sport, raw: p, bucket: 'tomorrow' })
  }
  return out
}

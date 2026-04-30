export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

export function formatPercentRaw(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toFixed(digits)}%`
}

export function formatSignedPercent(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  const v = value * 100
  const sign = v >= 0 ? '+' : ''
  return `${sign}${v.toFixed(digits)}%`
}

export function formatUnits(value: number | null | undefined, digits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}`
}

export function formatUnitSize(unitSize: number | null | undefined): string {
  if (unitSize == null || !Number.isFinite(unitSize)) return '—'
  return `${(unitSize * 100).toFixed(1)}u`
}

export function formatPickLabel(pick: string, betLine: string | null | undefined, awayAbbr?: string | null, homeAbbr?: string | null): string {
  if (pick === 'No Pick' || !pick) return 'No Pick'
  const team = pick === 'Away' ? (awayAbbr || 'AWAY') : pick === 'Home' ? (homeAbbr || 'HOME') : pick
  if (betLine) return `${team} ${betLine}`
  return team
}

export function formatDateShort(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso + 'T00:00:00')
    if (Number.isNaN(d.getTime())) return iso
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return iso
  }
}

export function formatSportLabel(key: string): string {
  return key.toUpperCase()
}

/**
 * ESPN CDN logo URL helpers.
 *
 * Team logos:  https://a.espncdn.com/i/teamlogos/{league}/500/{abbr}.png
 * League marks: https://a.espncdn.com/i/teamlogos/leagues/500/{league}.png
 *
 * `null` means "no good ESPN URL" — call sites render a monogram fallback.
 */

const ESPN_BASE = 'https://a.espncdn.com/i/teamlogos'

const TEAM_LOGO_LEAGUES: Record<string, string> = {
  nba: 'nba',
  nfl: 'nfl',
  nhl: 'nhl',
  mlb: 'mlb',
  mls: 'soccer/clubs',
  wnba: 'wnba',
}

const SPORT_MARK_LEAGUES: Record<string, string> = {
  nba: 'nba',
  nfl: 'nfl',
  nhl: 'nhl',
  mlb: 'mlb',
  mls: 'mls',
  wnba: 'wnba',
  ncaaf: 'ncaa',
  ncaab: 'ncaa',
  cfl: 'cfl',
}

// Few SBR↔ESPN abbreviation differences. Keep this list small — anything
// missing falls through to the monogram, which is acceptable.
const ABBR_ALIASES: Record<string, Record<string, string>> = {
  nba: {
    BRK: 'bkn',
    BKN: 'bkn',
    PHO: 'phx',
    CHA: 'cha',
    GS: 'gs',
    NO: 'no',
    NY: 'ny',
    SA: 'sa',
  },
  nfl: {
    JAC: 'jax',
    LAR: 'lar',
    LV: 'lv',
    OAK: 'lv',
    SD: 'lac',
    STL: 'lar',
    WSH: 'wsh',
    WAS: 'wsh',
  },
  nhl: {
    LAK: 'la',
    LA: 'la',
    SJS: 'sj',
    TBL: 'tb',
    NJD: 'nj',
    VGK: 'vgk',
  },
  mlb: {
    CWS: 'cws',
    KCR: 'kc',
    SDP: 'sd',
    SFG: 'sf',
    TBR: 'tb',
    WSN: 'wsh',
  },
  wnba: {},
  mls: {},
}

function normalizeAbbr(sport: string, abbr: string): string {
  const upper = abbr.trim().toUpperCase()
  const aliases = ABBR_ALIASES[sport] ?? {}
  if (aliases[upper]) return aliases[upper]
  return upper.toLowerCase()
}

export function teamLogoUrl(sport: string | null | undefined, abbr: string | null | undefined): string | null {
  if (!sport || !abbr) return null
  const key = sport.toLowerCase()
  const slug = TEAM_LOGO_LEAGUES[key]
  if (!slug) return null
  const normalized = normalizeAbbr(key, abbr)
  if (!normalized) return null
  return `${ESPN_BASE}/${slug}/500/${normalized}.png`
}

export function sportLogoUrl(sport: string | null | undefined): string | null {
  if (!sport) return null
  const key = sport.toLowerCase()
  const slug = SPORT_MARK_LEAGUES[key]
  if (!slug) return null
  return `${ESPN_BASE}/leagues/500/${slug}.png`
}

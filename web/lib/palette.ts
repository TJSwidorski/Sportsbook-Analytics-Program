export interface Palette {
  bg: string
  surface: string
  surface2: string
  border: string
  border2: string
  text: string
  muted: string
  accent: string
  accentDim: string
  danger: string
  blue: string
  blueDim: string
}

export const TERMINAL_DEFAULTS = {
  greenHue: 145,
  blueHue: 250,
  accentChroma: 0.16,
  meshDensity: 75,
  blueAccentStrength: 60,
} as const

export function getPalette(dark: boolean): Palette {
  const { greenHue, blueHue, accentChroma } = TERMINAL_DEFAULTS
  if (dark) {
    return {
      bg: '#0a0d12',
      surface: '#10141b',
      surface2: '#161b25',
      border: 'rgba(255,255,255,0.08)',
      border2: 'rgba(255,255,255,0.14)',
      text: '#e8edf5',
      muted: '#7c8597',
      accent: `oklch(0.72 ${accentChroma} ${greenHue})`,
      accentDim: `oklch(0.5 ${accentChroma * 0.75} ${greenHue})`,
      danger: 'oklch(0.68 0.2 25)',
      blue: `oklch(0.72 ${accentChroma * 1.1} ${blueHue})`,
      blueDim: `oklch(0.5 ${accentChroma * 0.8} ${blueHue})`,
    }
  }
  return {
    bg: '#fafbfc',
    surface: '#ffffff',
    surface2: '#f4f6f9',
    border: 'rgba(15,20,30,0.08)',
    border2: 'rgba(15,20,30,0.14)',
    text: '#0d1320',
    muted: '#5c6473',
    accent: `oklch(0.55 ${accentChroma} ${greenHue})`,
    accentDim: `oklch(0.7 ${accentChroma * 0.6} ${greenHue})`,
    danger: 'oklch(0.58 0.22 25)',
    blue: `oklch(0.5 ${accentChroma * 1.1} ${blueHue})`,
    blueDim: `oklch(0.7 ${accentChroma * 0.6} ${blueHue})`,
  }
}

export const FONT_SANS = "'IBM Plex Sans', system-ui, sans-serif"
export const FONT_MONO = "'JetBrains Mono', ui-monospace, monospace"

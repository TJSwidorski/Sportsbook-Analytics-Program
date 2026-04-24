import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary':   '#070B14',
        'bg-surface':   '#0D1525',
        'bg-elevated':  '#142038',
        'border-subtle':'#1E3055',
        'border-def':   '#2A4580',
        'txt-primary':  '#E2EAFF',
        'txt-secondary':'#7A92C0',
        'txt-muted':    '#3D5280',
        mint:    '#00E896',
        amber:   '#FFA82E',
        crimson: '#FF3B5C',
        royal:   '#3D8BFF',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        mono:    ['"JetBrains Mono"', 'Menlo', 'monospace'],
        sans:    ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'border-beam':    'border-beam calc(var(--duration)*1s) infinite linear',
        'fade-up':        'fade-up 0.6s ease-out forwards',
        'spin-slow':      'spin 20s linear infinite',
        'spin-slow-rev':  'spin 28s linear infinite reverse',
        'spin-slowest':   'spin 38s linear infinite',
        'pulse-soft':     'pulse-soft 3s ease-in-out infinite',
      },
      keyframes: {
        'border-beam': {
          '100%': { 'offset-distance': '100%' },
        },
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}

export default config

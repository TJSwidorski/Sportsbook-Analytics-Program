'use client'

import type { Palette } from '@/lib/palette'
import { FONT_MONO } from '@/lib/palette'
import type { RecentPick } from '@/lib/use-recent-picks'
import { formatDateShort } from '@/lib/formatters'

interface Props {
  palette: Palette
  picks: RecentPick[]
  title?: string
}

export function RecentPicksTable({ palette, picks, title = 'PICK LOG / RECENT' }: Props) {
  return (
    <div style={{ background: palette.surface, border: `1px solid ${palette.border}` }}>
      <div style={{ padding: '20px 24px 12px', borderBottom: `1px solid ${palette.border}` }}>
        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
            letterSpacing: 1.5,
          }}
        >
          {title}
        </div>
      </div>
      {picks.length === 0 ? (
        <div
          style={{
            padding: 24,
            fontFamily: FONT_MONO,
            fontSize: 11,
            color: palette.muted,
          }}
        >
          NO SETTLED PICKS YET. The prefetch logs picks daily; results appear here once games complete.
        </div>
      ) : (
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontFamily: FONT_MONO,
            fontSize: 12,
          }}
        >
          <thead>
            <tr style={{ color: palette.muted, fontSize: 10, letterSpacing: 1 }}>
              <th style={{ padding: '10px 24px', textAlign: 'left', fontWeight: 400 }}>DATE</th>
              <th style={{ padding: '10px 0', textAlign: 'left', fontWeight: 400 }}>LEAGUE</th>
              <th style={{ padding: '10px 0', textAlign: 'left', fontWeight: 400 }}>MATCH</th>
              <th style={{ padding: '10px 0', textAlign: 'left', fontWeight: 400 }}>PICK</th>
              <th style={{ padding: '10px 24px', textAlign: 'right', fontWeight: 400 }}>RES</th>
              <th style={{ padding: '10px 24px 10px 0', textAlign: 'right', fontWeight: 400 }}>U</th>
            </tr>
          </thead>
          <tbody>
            {picks.map((p, i) => {
              const isWin = p.result === 'W'
              const isLoss = p.result === 'L'
              const units = p.units ?? 0
              const unitsStr = `${units >= 0 ? '+' : ''}${units.toFixed(2)}`
              const pickLabel = p.bet_line && p.pick !== 'No Pick' ? `${p.pick} ${p.bet_line}` : p.pick
              return (
                <tr key={i} style={{ borderTop: `1px solid ${palette.border}` }}>
                  <td style={{ padding: '10px 24px', color: palette.muted }}>{formatDateShort(p.date)}</td>
                  <td style={{ padding: '10px 0', color: palette.muted }}>{p.sport.toUpperCase()}</td>
                  <td style={{ padding: '10px 0' }}>{p.matchup}</td>
                  <td style={{ padding: '10px 0', color: palette.text }}>{pickLabel}</td>
                  <td
                    style={{
                      padding: '10px 24px',
                      textAlign: 'right',
                      color: isWin ? palette.accent : isLoss ? palette.danger : palette.muted,
                      fontWeight: 600,
                    }}
                  >
                    {p.result ?? '—'}
                  </td>
                  <td
                    style={{
                      padding: '10px 24px 10px 0',
                      textAlign: 'right',
                      color: units > 0 ? palette.accent : units < 0 ? palette.danger : palette.muted,
                    }}
                  >
                    {unitsStr}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}

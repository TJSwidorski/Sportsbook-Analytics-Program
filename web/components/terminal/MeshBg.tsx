'use client'

import { useEffect, useMemo, useRef, type RefObject } from 'react'

interface MeshNode {
  bx: number
  by: number
  ox: number
  oy: number
  phase: number
  speed: number
  amp: number
  x: number
  y: number
  pulse: number
}

interface MeshState {
  nodes: MeshNode[]
  cols: number
  rows: number
  w: number
  h: number
  scrollY: number
  t: number
}

interface MeshBgProps {
  dark?: boolean
  accentA?: string
  accentB?: string
  scrollEl?: RefObject<HTMLElement | null> | null
}

export function MeshBg({ dark = false, accentA, accentB, scrollEl = null }: MeshBgProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const rafRef = useRef(0)
  const stateRef = useRef<MeshState>({
    nodes: [],
    cols: 0,
    rows: 0,
    w: 0,
    h: 0,
    scrollY: 0,
    t: 0,
  })

  const palette = useMemo(
    () => ({
      edge: dark ? 'rgba(180,200,220,0.18)' : 'rgba(20,30,45,0.22)',
      node: dark ? 'rgba(220,235,250,0.7)' : 'rgba(20,30,45,0.55)',
      glow: accentA || 'oklch(0.62 0.2 250)',
      halo: accentB || 'oklch(0.7 0.18 145)',
    }),
    [dark, accentA, accentB],
  )

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)

    const resize = () => {
      const r = canvas.getBoundingClientRect()
      canvas.width = r.width * dpr
      canvas.height = r.height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const cols = 14
      const rows = 10
      const w = r.width
      const h = r.height
      const nodes: MeshNode[] = []
      for (let i = 0; i <= cols; i++) {
        for (let j = 0; j <= rows; j++) {
          const jitter = 0.08
          const baseX = (i / cols) * w
          const baseY = (j / rows) * h
          nodes.push({
            bx: baseX,
            by: baseY,
            ox: ((Math.random() - 0.5) * w) / cols * jitter,
            oy: ((Math.random() - 0.5) * h) / rows * jitter,
            phase: Math.random() * Math.PI * 2,
            speed: 0.0003 + Math.random() * 0.0006,
            amp: 4,
            x: 0,
            y: 0,
            pulse: Math.random(),
          })
        }
      }
      stateRef.current.nodes = nodes
      stateRef.current.cols = cols
      stateRef.current.rows = rows
      stateRef.current.w = w
      stateRef.current.h = h
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    const onScroll = () => {
      const target = scrollEl?.current ?? null
      stateRef.current.scrollY = target ? target.scrollTop : window.scrollY
    }
    const target: HTMLElement | Window | null = scrollEl?.current ?? null
    if (target) target.addEventListener('scroll', onScroll, { passive: true })
    else window.addEventListener('scroll', onScroll, { passive: true })

    const tick = () => {
      const s = stateRef.current
      s.t += 1
      const { nodes, cols, rows, w, h } = s
      if (!nodes.length || !w) {
        rafRef.current = requestAnimationFrame(tick)
        return
      }
      ctx.clearRect(0, 0, w, h)

      const sy = s.scrollY * 0.05
      for (const n of nodes) {
        const drift = Math.sin(s.t * n.speed + n.phase) * n.amp
        const drift2 = Math.cos(s.t * n.speed * 0.7 + n.phase) * n.amp
        n.x = n.bx + n.ox + drift + Math.sin(sy * 0.01 + n.phase) * 6
        n.y = n.by + n.oy + drift2 - sy * 0.15
      }

      ctx.strokeStyle = palette.edge
      ctx.lineWidth = 0.5
      for (let i = 0; i <= cols; i++) {
        for (let j = 0; j <= rows; j++) {
          const idx = i * (rows + 1) + j
          const n = nodes[idx]
          if (!n) continue
          if (i < cols) {
            const r = nodes[(i + 1) * (rows + 1) + j]
            if (r) {
              ctx.beginPath()
              ctx.moveTo(n.x, n.y)
              ctx.lineTo(r.x, r.y)
              ctx.stroke()
            }
          }
          if (j < rows) {
            const d = nodes[i * (rows + 1) + (j + 1)]
            if (d) {
              ctx.beginPath()
              ctx.moveTo(n.x, n.y)
              ctx.lineTo(d.x, d.y)
              ctx.stroke()
            }
          }
        }
      }

      for (const n of nodes) {
        const pulse = (Math.sin(s.t * 0.02 + n.phase * 3) + 1) * 0.5
        ctx.fillStyle = palette.node
        ctx.beginPath()
        ctx.arc(n.x, n.y, 1.2 + pulse * 0.6, 0, Math.PI * 2)
        ctx.fill()
      }

      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(rafRef.current)
      ro.disconnect()
      if (target) target.removeEventListener('scroll', onScroll)
      else window.removeEventListener('scroll', onScroll)
    }
  }, [palette, scrollEl])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  )
}

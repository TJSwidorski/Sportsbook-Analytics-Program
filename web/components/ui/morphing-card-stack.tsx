'use client'

import { useState, type ReactNode } from 'react'
import { motion, AnimatePresence, LayoutGroup, type PanInfo } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Grid3X3, Layers, LayoutList } from 'lucide-react'

export type LayoutMode = 'stack' | 'grid' | 'list'

export interface PickCardData {
  id: string
  title: string
  pick: string          // 'Away' | 'Home' | 'No Pick'
  confidence: number | null
  awayProb: number | null
  homeProb: number | null
  awayLines: string[]
  homeLines: string[]
  icon?: ReactNode
}

export interface MorphingCardStackProps {
  cards?: PickCardData[]
  className?: string
  defaultLayout?: LayoutMode
  onCardClick?: (card: PickCardData) => void
}

const layoutIcons = { stack: Layers, grid: Grid3X3, list: LayoutList }
const SWIPE_THRESHOLD = 50

function PickBadge({ pick }: { pick: string }) {
  if (pick === 'Away')
    return (
      <span className="inline-flex items-center gap-1 text-xs font-mono-data font-semibold text-mint">
        ↑ AWAY
      </span>
    )
  if (pick === 'Home')
    return (
      <span className="inline-flex items-center gap-1 text-xs font-mono-data font-semibold text-royal">
        ↓ HOME
      </span>
    )
  return (
    <span className="inline-flex items-center gap-1 text-xs font-mono-data text-txt-muted">
      — NO PICK
    </span>
  )
}

function ConfidenceBar({ confidence }: { confidence: number | null }) {
  if (confidence === null) return null
  const pct = Math.round(confidence * 100)
  const color = pct >= 65 ? '#00E896' : pct >= 50 ? '#FFA82E' : '#FF3B5C'
  return (
    <div className="mt-2">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-txt-muted uppercase tracking-widest">Confidence</span>
        <span className="text-[10px] font-mono-data" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-0.5 rounded-full bg-border-subtle overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}

export function MorphingCardStack({
  cards = [],
  className,
  defaultLayout = 'stack',
  onCardClick,
}: MorphingCardStackProps) {
  const [layout, setLayout] = useState<LayoutMode>(defaultLayout)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [isDragging, setIsDragging] = useState(false)

  if (!cards || cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-txt-muted">
        <span className="text-4xl mb-2">—</span>
        <p className="text-sm font-mono-data">No games today</p>
      </div>
    )
  }

  const handleDragEnd = (_: unknown, info: PanInfo) => {
    const { offset, velocity } = info
    const swipe = Math.abs(offset.x) * velocity.x
    if (offset.x < -SWIPE_THRESHOLD || swipe < -1000) {
      setActiveIndex((prev) => (prev + 1) % cards.length)
    } else if (offset.x > SWIPE_THRESHOLD || swipe > 1000) {
      setActiveIndex((prev) => (prev - 1 + cards.length) % cards.length)
    }
    setIsDragging(false)
  }

  const getStackOrder = () => {
    const reordered = []
    for (let i = 0; i < cards.length; i++) {
      const index = (activeIndex + i) % cards.length
      reordered.push({ ...cards[index], stackPosition: i })
    }
    return reordered.reverse()
  }

  const getLayoutStyles = (stackPosition: number) => {
    switch (layout) {
      case 'stack':
        return { top: stackPosition * 8, left: stackPosition * 8, zIndex: cards.length - stackPosition, rotate: (stackPosition - 1) * 1.5 }
      default:
        return { top: 0, left: 0, zIndex: 1, rotate: 0 }
    }
  }

  const containerStyles = { stack: 'relative h-72 w-72', grid: 'grid grid-cols-2 gap-3', list: 'flex flex-col gap-3' }
  const displayCards = layout === 'stack' ? getStackOrder() : cards.map((c, i) => ({ ...c, stackPosition: i }))

  return (
    <div className={cn('space-y-4', className)}>
      {/* Layout toggle */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-txt-muted font-mono-data uppercase tracking-widest">
          {cards.length} game{cards.length !== 1 ? 's' : ''}
        </p>
        <div className="flex items-center gap-1 rounded-lg bg-bg-elevated border border-border-subtle p-1">
          {(Object.keys(layoutIcons) as LayoutMode[]).map((mode) => {
            const Icon = layoutIcons[mode]
            return (
              <button
                key={mode}
                onClick={() => setLayout(mode)}
                className={cn(
                  'rounded-md p-1.5 transition-all',
                  layout === mode ? 'bg-mint text-bg-primary' : 'text-txt-muted hover:text-txt-secondary',
                )}
                aria-label={`${mode} view`}
              >
                <Icon className="h-3.5 w-3.5" />
              </button>
            )
          })}
        </div>
      </div>

      {/* Cards */}
      <LayoutGroup>
        <motion.div layout className={cn(containerStyles[layout], 'mx-auto')}>
          <AnimatePresence mode="popLayout">
            {displayCards.map((card) => {
              const styles = getLayoutStyles(card.stackPosition)
              const isExpanded = expandedCard === card.id
              const isTopCard = layout === 'stack' && card.stackPosition === 0
              const pickColor = card.pick === 'Away' ? '#00E896' : card.pick === 'Home' ? '#3D8BFF' : '#3D5280'

              return (
                <motion.div
                  key={card.id}
                  layoutId={card.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: isExpanded ? 1.03 : 1, x: 0, ...styles }}
                  exit={{ opacity: 0, scale: 0.85, x: -200 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                  drag={isTopCard ? 'x' : false}
                  dragConstraints={{ left: 0, right: 0 }}
                  dragElastic={0.7}
                  onDragStart={() => setIsDragging(true)}
                  onDragEnd={handleDragEnd}
                  whileDrag={{ scale: 1.02, cursor: 'grabbing' }}
                  onClick={() => {
                    if (isDragging) return
                    setExpandedCard(isExpanded ? null : card.id)
                    onCardClick?.(card)
                  }}
                  className={cn(
                    'cursor-pointer rounded-xl border bg-bg-surface text-txt-primary',
                    'hover:border-border-def transition-colors',
                    layout === 'stack' && 'absolute w-60 h-[17rem]',
                    layout === 'stack' && isTopCard && 'cursor-grab active:cursor-grabbing',
                    layout === 'grid' && 'w-full aspect-square',
                    layout === 'list' && 'w-full',
                    isExpanded ? 'border-mint/40' : 'border-border-subtle',
                  )}
                  style={{ borderColor: isExpanded ? pickColor + '40' : undefined }}
                >
                  <div className="p-4 h-full flex flex-col">
                    {/* Game label */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[10px] font-mono-data text-txt-muted uppercase tracking-widest">
                        {card.title}
                      </span>
                      <div
                        className="w-2 h-2 rounded-full animate-pulse-soft"
                        style={{ backgroundColor: pickColor }}
                      />
                    </div>

                    {/* Pick direction — large display */}
                    <div className="flex-1 flex flex-col justify-center">
                      <p
                        className="font-display text-5xl font-semibold italic leading-none mb-1"
                        style={{ color: pickColor }}
                      >
                        {card.pick === 'Away' ? '↑' : card.pick === 'Home' ? '↓' : '—'}
                      </p>
                      <PickBadge pick={card.pick} />
                    </div>

                    <ConfidenceBar confidence={card.confidence} />

                    {/* Top lines */}
                    {(card.awayLines.length > 0 || card.homeLines.length > 0) && (
                      <div className="mt-3 pt-3 border-t border-border-subtle grid grid-cols-2 gap-2">
                        <div>
                          <p className="text-[9px] text-txt-muted uppercase tracking-widest mb-1">Away</p>
                          <p className="text-xs font-mono-data text-txt-secondary">
                            {card.awayLines[0] || '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-[9px] text-txt-muted uppercase tracking-widest mb-1">Home</p>
                          <p className="text-xs font-mono-data text-txt-secondary">
                            {card.homeLines[0] || '—'}
                          </p>
                        </div>
                      </div>
                    )}

                    {isTopCard && layout === 'stack' && (
                      <p className="text-[9px] text-center text-txt-muted mt-2 opacity-50">
                        swipe to navigate
                      </p>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </motion.div>
      </LayoutGroup>

      {/* Stack dots */}
      {layout === 'stack' && cards.length > 1 && (
        <div className="flex justify-center gap-1.5 pt-2">
          {cards.map((_, index) => (
            <button
              key={index}
              onClick={() => setActiveIndex(index)}
              className={cn(
                'h-1 rounded-full transition-all',
                index === activeIndex ? 'w-4 bg-mint' : 'w-1 bg-border-def hover:bg-txt-muted',
              )}
              aria-label={`Game ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}

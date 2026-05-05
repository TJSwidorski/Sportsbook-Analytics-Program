'use client'

import { useEffect, useState } from 'react'
import type { Palette } from '@/lib/palette'
import { sportLogoUrl } from '@/lib/logos'

interface Props {
  palette: Palette
  sport: string
  size?: number
}

export function SportMark({ palette, sport, size = 14 }: Props) {
  const url = sportLogoUrl(sport)
  const [errored, setErrored] = useState(false)

  useEffect(() => {
    setErrored(false)
  }, [url])

  if (url && !errored) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={url}
        alt={`${sport} logo`}
        width={size}
        height={size}
        loading="lazy"
        decoding="async"
        onError={() => setErrored(true)}
        style={{
          width: size,
          height: size,
          objectFit: 'contain',
          display: 'inline-block',
          verticalAlign: 'middle',
        }}
      />
    )
  }

  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        display: 'inline-block',
        verticalAlign: 'middle',
        background: palette.muted,
        opacity: 0.6,
        borderRadius: '50%',
      }}
    />
  )
}

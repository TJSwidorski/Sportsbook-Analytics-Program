import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-10 w-full rounded-lg border border-border-subtle bg-bg-elevated px-3 py-2',
        'text-sm text-txt-primary font-mono-data placeholder:text-txt-muted',
        'transition-colors focus-visible:outline-none focus-visible:border-mint/50',
        'focus-visible:ring-2 focus-visible:ring-mint/20',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

export { Input }

import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mint/50 disabled:pointer-events-none disabled:opacity-40',
  {
    variants: {
      variant: {
        default:
          'bg-mint text-bg-primary font-semibold hover:bg-mint/90 shadow-[0_0_20px_rgba(0,232,150,0.3)]',
        secondary:
          'bg-bg-elevated border border-border-subtle text-txt-primary hover:border-border-def hover:bg-bg-elevated/80',
        ghost:
          'text-txt-secondary hover:text-txt-primary hover:bg-bg-elevated/60',
        outline:
          'border border-border-def text-txt-primary hover:bg-bg-elevated',
        destructive:
          'bg-crimson/10 border border-crimson/30 text-crimson hover:bg-crimson/20',
      },
      size: {
        default: 'h-10 px-5 py-2',
        sm:      'h-8 px-3 py-1.5 text-xs',
        lg:      'h-12 px-8 py-3 text-base',
        icon:    'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }

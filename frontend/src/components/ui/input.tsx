import type { InputHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'h-9 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:border-forecast focus:ring-2 focus:ring-forecast/20',
        className,
      )}
      {...props}
    />
  )
}

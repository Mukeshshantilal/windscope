import type { SelectHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

export function NativeSelect({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        'h-9 rounded-md border border-line bg-white px-2 text-sm text-ink outline-none focus:border-forecast focus:ring-2 focus:ring-forecast/20',
        className,
      )}
      {...props}
    />
  )
}

import { cn } from './cn'

interface SkeletonProps {
  className?: string
  height?: string
  width?: string
}

export function Skeleton({ className, height, width }: SkeletonProps) {
  return (
    <div
      className={cn('skeleton rounded-md', className)}
      style={{ height, width }}
      aria-hidden="true"
    />
  )
}

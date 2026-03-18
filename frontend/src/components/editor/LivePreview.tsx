import { useEffect, useRef } from 'react'
import { useEditorStore } from '../../store/editorStore'
import { formatTimecode } from '../../types'

export function LivePreview() {
  const liveSegments = useEditorStore(s => s.liveSegments)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liveSegments])

  if (liveSegments.length === 0) return null

  return (
    <div
      aria-live="polite"
      aria-label="Live transcription preview"
      className="max-h-48 overflow-y-auto rounded-md border border-[--color-border] bg-[--color-surface-raised] p-2"
    >
      {liveSegments.map((seg) => (
        <div key={seg.index} className="flex gap-3 py-0.5 text-sm">
          <span className="shrink-0 font-mono text-xs text-[--color-text-muted] pt-px">
            {formatTimecode(seg.start)}
          </span>
          <span className="text-[--color-text]">{seg.text}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

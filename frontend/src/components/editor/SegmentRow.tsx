import { useState } from 'react'
import type { Segment } from '../../types'
import { formatTimecode } from '../../types'
import { cn } from '../ui/cn'

interface SegmentRowProps {
  segment: Segment
  onEdit: (index: number, text: string) => void
  editing?: boolean
  highlighted?: boolean
  onClick?: () => void
}

export function SegmentRow({ segment, onEdit, editing = false, highlighted = false, onClick }: SegmentRowProps) {
  const [draft, setDraft] = useState(segment.text)
  const [lastText, setLastText] = useState(segment.text)

  // Sync draft when segment.text changes externally (e.g. after translation)
  // Uses setState-during-render pattern (React 18+) to avoid useEffect loop
  if (!editing && segment.text !== lastText) {
    setDraft(segment.text)
    setLastText(segment.text)
  }

  const handleBlur = () => {
    onEdit(segment.index, draft)
  }

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-2 border-b border-neutral-100 cursor-pointer hover:bg-neutral-50 transition-colors',
        highlighted && 'bg-yellow-50',
        editing && 'bg-blue-50 cursor-default',
      )}
      onClick={!editing ? onClick : undefined}
    >
      <div className="flex-shrink-0 w-6 text-xs text-neutral-400 pt-1 text-right select-none">
        {segment.index + 1}
      </div>
      <div className="flex-shrink-0 flex flex-col gap-0.5 text-xs text-neutral-500 font-mono pt-0.5">
        <span>{formatTimecode(segment.start)}</span>
        <span>{formatTimecode(segment.end)}</span>
      </div>
      <div className="flex-1 min-w-0">
        {segment.speaker && (
          <p className="text-xs font-medium text-blue-600 mb-0.5">{segment.speaker}</p>
        )}
        {editing ? (
          <textarea
            className="w-full resize-none text-sm text-neutral-800 bg-transparent border-0 outline-none focus:ring-0 p-0"
            rows={2}
            value={draft}
            autoFocus
            onChange={e => setDraft(e.target.value)}
            onBlur={handleBlur}
          />
        ) : (
          <p className="text-sm text-neutral-800 leading-snug">{segment.text}</p>
        )}
      </div>
    </div>
  )
}

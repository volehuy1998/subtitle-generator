import { useEditorStore } from '../../store/editorStore'
import { api } from '../../api/client'
import { SegmentRow } from './SegmentRow'
import { EmptyState } from '../ui/EmptyState'

interface SegmentListProps {
  taskId: string
}

export function SegmentList({ taskId }: SegmentListProps) {
  const segments = useEditorStore(s => s.segments)
  const searchResults = useEditorStore(s => s.searchResults)
  const editingSegmentIndex = useEditorStore(s => s.editingSegmentIndex)
  const setEditingSegment = useEditorStore(s => s.setEditingSegment)
  const updateSegment = useEditorStore(s => s.updateSegment)

  const handleEdit = (index: number, text: string) => {
    updateSegment(index, text)
    api.updateSubtitle(taskId, index, text).catch(() => {
      // fire-and-forget — errors silently ignored for now
    })
  }

  if (segments.length === 0) {
    return <EmptyState title="No subtitles yet" />
  }

  return (
    <div data-testid="segment-list" className="max-h-[60vh] overflow-y-auto">
      {segments.map((segment, i) => (
        <SegmentRow
          key={segment.index}
          segment={segment}
          editing={editingSegmentIndex === i}
          highlighted={searchResults.some(r => r.segmentIndex === i)}
          onClick={() => setEditingSegment(i)}
          onEdit={(idx, text) => handleEdit(idx, text)}
        />
      ))}
    </div>
  )
}

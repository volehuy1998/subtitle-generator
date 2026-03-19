/**
 * BulkEditBar — floating toolbar for multi-segment operations.
 * Appears when one or more segments are selected via checkbox.
 * Supports find & replace across selected segments and bulk delete.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useState } from 'react'
import { useEditorStore } from '../../store/editorStore'
import { Button } from '../ui/Button'

export function BulkEditBar() {
  const selectedSegments = useEditorStore(s => s.selectedSegments)
  const segments = useEditorStore(s => s.segments)
  const setSegments = useEditorStore(s => s.setSegments)
  const selectAll = useEditorStore(s => s.selectAll)
  const clearSelection = useEditorStore(s => s.clearSelection)
  const [findText, setFindText] = useState('')
  const [replaceText, setReplaceText] = useState('')

  if (selectedSegments.size === 0) return null

  const handleReplace = () => {
    if (!findText) return
    const updated = segments.map((seg, i) =>
      selectedSegments.has(i)
        ? { ...seg, text: seg.text.replaceAll(findText, replaceText) }
        : seg
    )
    setSegments(updated)
  }

  const handleDelete = () => {
    const updated = segments.filter((_, i) => !selectedSegments.has(i))
    setSegments(updated)
    clearSelection()
  }

  return (
    <div className="sticky top-14 z-30 bg-[var(--color-surface)] border-b border-[var(--color-border)] px-4 py-2 flex items-center gap-3 shadow-sm animate-fade-in">
      <span className="text-sm font-medium text-[var(--color-text)]">
        {selectedSegments.size} selected
      </span>
      <button
        type="button"
        onClick={selectAll}
        className="text-xs text-[var(--color-primary)] hover:underline"
      >
        Select all
      </button>
      <button
        type="button"
        onClick={clearSelection}
        className="text-xs text-[var(--color-text-muted)] hover:underline"
      >
        Clear
      </button>
      <div className="flex-1" />
      <input
        type="text"
        value={findText}
        onChange={e => setFindText(e.target.value)}
        placeholder="Find..."
        className="h-7 w-28 px-2 text-xs bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-[var(--color-text)]"
      />
      <input
        type="text"
        value={replaceText}
        onChange={e => setReplaceText(e.target.value)}
        placeholder="Replace..."
        className="h-7 w-28 px-2 text-xs bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-[var(--color-text)]"
      />
      <Button variant="secondary" size="sm" onClick={handleReplace} disabled={!findText}>
        Replace
      </Button>
      <Button variant="danger" size="sm" onClick={handleDelete}>
        Delete
      </Button>
    </div>
  )
}

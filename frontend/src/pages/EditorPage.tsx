/**
 * EditorPage — stub for Drop, See, Refine redesign.
 * Will be replaced with the full editor experience in a later task.
 *
 * — Pixel (Senior Frontend Engineer)
 */

interface EditorPageProps {
  taskId: string
}

export function EditorPage({ taskId }: EditorPageProps) {
  return (
    <div className="p-8 text-center" style={{ color: 'var(--color-text-secondary)' }}>
      Editor {taskId} (coming soon)
    </div>
  )
}

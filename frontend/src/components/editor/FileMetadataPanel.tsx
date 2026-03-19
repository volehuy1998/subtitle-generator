import { useEditorStore } from '../../store/editorStore'
import { formatFileSize, formatDuration } from '../../types'

function MetadataRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  if (value == null || value === '') return null
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
      <span className="text-xs font-mono text-[var(--color-text)]">{value}</span>
    </div>
  )
}

export function FileMetadataPanel() {
  const meta = useEditorStore((s) => s.fileMetadata)

  if (!meta) return null

  return (
    <div className="space-y-1 divide-y divide-[var(--color-border)]">
      <div className="pb-2">
        <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">File</h4>
        <MetadataRow label="Name" value={meta.filename} />
        <MetadataRow label="Size" value={meta.size ? formatFileSize(meta.size) : undefined} />
        <MetadataRow label="Format" value={meta.format} />
        <MetadataRow label="Duration" value={meta.duration ? formatDuration(meta.duration) : undefined} />
      </div>
      {meta.isVideo && (
        <div className="pt-2">
          <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-2">Video</h4>
          <MetadataRow label="Resolution" value={meta.resolution} />
          <MetadataRow label="Codec" value={meta.codec} />
        </div>
      )}
    </div>
  )
}

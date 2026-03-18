import { useState } from 'react'
import { RefreshCw, Languages, Film, Search } from 'lucide-react'
import { Button } from '../ui/Button'
import { IconButton } from '../ui/IconButton'
import { Badge } from '../ui/Badge'
import { DownloadMenu } from './DownloadMenu'
import { RetranscribeDialog } from './RetranscribeDialog'
import { useEditorStore } from '../../store/editorStore'
import { useUIStore } from '../../store/uiStore'

export function EditorToolbar() {
  const taskId = useEditorStore(s => s.taskId)
  const fileMetadata = useEditorStore(s => s.fileMetadata)
  const isVideo = useEditorStore(s => s.isVideo)
  const language = useEditorStore(s => s.language)
  const modelUsed = useEditorStore(s => s.modelUsed)
  const setContextPanel = useUIStore(s => s.setContextPanel)
  const [retranscribeOpen, setRetranscribeOpen] = useState(false)

  if (!taskId) return null

  return (
    <>
      <div className="flex items-center justify-between gap-3 px-4 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        {/* Left: actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <DownloadMenu taskId={taskId} />

          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Languages className="h-3.5 w-3.5" />}
            onClick={() => setContextPanel('translate')}
          >
            Translate
          </Button>

          {isVideo && (
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<Film className="h-3.5 w-3.5" />}
              onClick={() => setContextPanel('embed')}
            >
              Embed
            </Button>
          )}

          <IconButton
            icon={<Search className="h-4 w-4" />}
            aria-label="Search subtitles"
            variant="ghost"
            size="sm"
            title="Search subtitles"
            onClick={() => setContextPanel('search')}
          />

          <IconButton
            icon={<RefreshCw className="h-4 w-4" />}
            aria-label="Re-transcribe"
            variant="ghost"
            size="sm"
            title="Re-transcribe"
            onClick={() => setRetranscribeOpen(true)}
          />
        </div>

        {/* Right: metadata */}
        <div className="flex items-center gap-2 shrink-0">
          {fileMetadata?.filename && (
            <span
              className="text-sm text-[var(--color-text-secondary)] max-w-[200px] truncate"
              title={fileMetadata.filename}
            >
              {fileMetadata.filename}
            </span>
          )}
          {language && (
            <Badge variant="info">{language}</Badge>
          )}
          {modelUsed && (
            <Badge>{modelUsed}</Badge>
          )}
        </div>
      </div>

      <RetranscribeDialog
        open={retranscribeOpen}
        onClose={() => setRetranscribeOpen(false)}
        taskId={taskId}
      />
    </>
  )
}

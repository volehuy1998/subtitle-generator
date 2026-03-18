import { X } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { SmartSuggestion } from './SmartSuggestion'
import { TranslatePanel } from './TranslatePanel'
import { EmbedPanel } from './EmbedPanel'
import { useEditorStore } from '../../store/editorStore'
import { useUIStore } from '../../store/uiStore'

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function InfoPanel() {
  const fileMetadata = useEditorStore(s => s.fileMetadata)
  const language = useEditorStore(s => s.language)
  const modelUsed = useEditorStore(s => s.modelUsed)
  const segments = useEditorStore(s => s.segments)
  const timings = useEditorStore(s => s.timings)
  const setContextPanel = useUIStore(s => s.setContextPanel)

  const isNonEnglish = language && language.toLowerCase() !== 'en' && language.toLowerCase() !== 'english'

  return (
    <div className="flex flex-col gap-4">
      {/* File info */}
      <div className="rounded-lg border border-[--color-border] bg-[--color-surface-raised] p-3">
        <p className="text-xs font-semibold text-[--color-text-muted] uppercase tracking-wide mb-2">
          File Info
        </p>
        <dl className="flex flex-col gap-1.5 text-sm">
          {fileMetadata?.filename && (
            <div className="flex justify-between gap-2">
              <dt className="text-[--color-text-secondary] shrink-0">Name</dt>
              <dd className="text-[--color-text] truncate text-right" title={fileMetadata.filename}>
                {fileMetadata.filename}
              </dd>
            </div>
          )}
          {fileMetadata?.duration !== undefined && fileMetadata.duration > 0 && (
            <div className="flex justify-between gap-2">
              <dt className="text-[--color-text-secondary]">Duration</dt>
              <dd className="text-[--color-text]">{formatDuration(fileMetadata.duration)}</dd>
            </div>
          )}
          {language && (
            <div className="flex justify-between gap-2">
              <dt className="text-[--color-text-secondary]">Language</dt>
              <dd><Badge variant="info">{language}</Badge></dd>
            </div>
          )}
          {modelUsed && (
            <div className="flex justify-between gap-2">
              <dt className="text-[--color-text-secondary]">Model</dt>
              <dd><Badge>{modelUsed}</Badge></dd>
            </div>
          )}
        </dl>
      </div>

      {/* Stats */}
      {segments.length > 0 && (
        <div className="rounded-lg border border-[--color-border] bg-[--color-surface-raised] p-3">
          <p className="text-xs font-semibold text-[--color-text-muted] uppercase tracking-wide mb-2">
            Stats
          </p>
          <dl className="flex flex-col gap-1.5 text-sm">
            <div className="flex justify-between">
              <dt className="text-[--color-text-secondary]">Segments</dt>
              <dd className="text-[--color-text]">{segments.length}</dd>
            </div>
            {timings?.transcribe && (
              <div className="flex justify-between">
                <dt className="text-[--color-text-secondary]">Transcribe time</dt>
                <dd className="text-[--color-text]">{(timings.transcribe / 1000).toFixed(1)}s</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Smart suggestions */}
      {isNonEnglish && (
        <SmartSuggestion
          id="translate-non-english"
          title="Translate this content"
          description={`Detected language: ${language}. Translate to English or another language.`}
          actionLabel="Open Translation"
          onAction={() => setContextPanel('translate')}
        />
      )}

      <SmartSuggestion
        id="try-embed"
        title="Embed subtitles into video"
        description="Burn subtitles directly into your video file for universal compatibility."
        actionLabel="Open Embed"
        onAction={() => setContextPanel('embed')}
      />
    </div>
  )
}

function SearchPanel() {
  const searchResults = useEditorStore(s => s.searchResults)
  const searchQuery = useEditorStore(s => s.searchQuery)

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-[--color-text-secondary]">
        {searchResults.length === 0
          ? searchQuery ? 'No results found.' : 'Enter a search query.'
          : `${searchResults.length} result${searchResults.length === 1 ? '' : 's'} found.`}
      </p>
      {searchResults.length > 0 && (
        <ul className="flex flex-col gap-2">
          {searchResults.map(r => (
            <li
              key={r.index}
              className="rounded-md border border-[--color-border] bg-[--color-surface-raised] p-2 text-sm"
            >
              <span className="text-xs text-[--color-text-muted] block mb-0.5">
                #{r.index + 1}
              </span>
              <span className="text-[--color-text]">{r.text}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function ContextPanel() {
  const contextPanelContent = useUIStore(s => s.contextPanelContent)
  const setContextPanel = useUIStore(s => s.setContextPanel)

  const titles: Record<typeof contextPanelContent, string> = {
    info: 'Info',
    translate: 'Translate',
    embed: 'Embed',
    search: 'Search',
  }

  return (
    <div className="w-full lg:w-[360px] border border-[--color-border] rounded-xl bg-[--color-surface] p-4 flex flex-col gap-3 h-fit">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[--color-text]">
          {titles[contextPanelContent]}
        </h2>
        {contextPanelContent !== 'info' && (
          <button
            className="p-1 rounded-md text-[--color-text-muted] hover:text-[--color-text] hover:bg-[--color-surface-raised] transition-colors"
            aria-label="Close panel"
            onClick={() => setContextPanel('info')}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Content */}
      {contextPanelContent === 'info' && <InfoPanel />}
      {contextPanelContent === 'translate' && <TranslatePanel />}
      {contextPanelContent === 'embed' && <EmbedPanel />}
      {contextPanelContent === 'search' && <SearchPanel />}
    </div>
  )
}

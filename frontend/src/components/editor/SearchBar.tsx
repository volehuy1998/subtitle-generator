import { useRef } from 'react'
import { Search } from 'lucide-react'
import { api } from '../../api/client'
import { useEditorStore } from '../../store/editorStore'
import { cn } from '../ui/cn'

interface SearchBarProps {
  taskId: string
}

export function SearchBar({ taskId }: SearchBarProps) {
  const searchResults = useEditorStore(s => s.searchResults)
  const setSearchResults = useEditorStore(s => s.setSearchResults)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    if (!query) {
      setSearchResults([])
      return
    }

    timerRef.current = setTimeout(() => {
      api.search(taskId, query).then(res => {
        const mapped = (res.matches ?? []).map(r => ({
          segmentIndex: r.index,
          text: r.text,
          matchStart: 0,
          matchEnd: 0,
        }))
        setSearchResults(mapped)
      }).catch(() => {
        // silently ignore search errors
      })
    }, 300)
  }

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400"
          size={16}
        />
        <input
          type="text"
          role="textbox"
          placeholder="Search subtitles..."
          onChange={handleChange}
          className={cn(
            'w-full pl-9 pr-3 py-2 text-sm rounded-md border border-neutral-200',
            'bg-white text-neutral-800 placeholder-neutral-400',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          )}
        />
      </div>
      {searchResults.length > 0 && (
        <span className="text-xs text-neutral-500 whitespace-nowrap">
          {searchResults.length} {searchResults.length === 1 ? 'match' : 'matches'}
        </span>
      )}
    </div>
  )
}

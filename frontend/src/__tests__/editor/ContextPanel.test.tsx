import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileMetadataPanel } from '../../components/editor/FileMetadataPanel'
import { useEditorStore } from '../../store/editorStore'

describe('FileMetadataPanel', () => {
  beforeEach(() => {
    useEditorStore.getState().reset()
  })

  it('renders nothing when no metadata is set', () => {
    const { container } = render(<FileMetadataPanel />)
    expect(container.innerHTML).toBe('')
  })

  it('renders file metadata rows', () => {
    useEditorStore.setState({
      fileMetadata: {
        filename: 'test-video.mp4',
        size: 10485760,
        format: 'mp4',
        duration: 125.5,
        resolution: '1920x1080',
        codec: 'h264',
        isVideo: true,
      },
    })
    render(<FileMetadataPanel />)
    expect(screen.getByText('Name')).toBeDefined()
    expect(screen.getByText('test-video.mp4')).toBeDefined()
    expect(screen.getByText('Format')).toBeDefined()
    expect(screen.getByText('mp4')).toBeDefined()
  })

  it('shows video section when isVideo is true', () => {
    useEditorStore.setState({
      fileMetadata: {
        filename: 'video.mp4',
        size: 5000000,
        format: 'mp4',
        duration: 60,
        resolution: '1280x720',
        codec: 'h264',
        isVideo: true,
      },
    })
    render(<FileMetadataPanel />)
    expect(screen.getByText('Video')).toBeDefined()
    expect(screen.getByText('Resolution')).toBeDefined()
    expect(screen.getByText('1280x720')).toBeDefined()
    expect(screen.getByText('Codec')).toBeDefined()
    expect(screen.getByText('h264')).toBeDefined()
  })

  it('hides video section when isVideo is false', () => {
    useEditorStore.setState({
      fileMetadata: {
        filename: 'audio.wav',
        size: 2000000,
        format: 'wav',
        duration: 30,
        resolution: null,
        codec: 'pcm',
        isVideo: false,
      },
    })
    render(<FileMetadataPanel />)
    expect(screen.queryByText('Video')).toBeNull()
    expect(screen.queryByText('Resolution')).toBeNull()
  })

  it('omits rows where value is null or empty', () => {
    useEditorStore.setState({
      fileMetadata: {
        filename: 'audio.wav',
        size: 0,
        format: 'wav',
        duration: 0,
        resolution: null,
        codec: '',
        isVideo: false,
      },
    })
    render(<FileMetadataPanel />)
    expect(screen.getByText('Name')).toBeDefined()
    expect(screen.queryByText('Resolution')).toBeNull()
    expect(screen.queryByText('Codec')).toBeNull()
  })
})

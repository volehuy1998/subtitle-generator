import { describe, it, expect } from 'vitest'
import { formatTimecode, formatFileSize, formatDuration, detectUploadType } from '../types'

describe('formatTimecode', () => {
  it('formats zero', () => expect(formatTimecode(0)).toBe('00:00:00'))
  it('formats seconds', () => expect(formatTimecode(65)).toBe('00:01:05'))
  it('formats hours', () => expect(formatTimecode(3661)).toBe('01:01:01'))
})

describe('formatFileSize', () => {
  it('formats bytes', () => expect(formatFileSize(500)).toBe('500 B'))
  it('formats KB', () => expect(formatFileSize(1536)).toBe('1.5 KB'))
  it('formats MB', () => expect(formatFileSize(245 * 1024 * 1024)).toBe('245.0 MB'))
  it('formats GB', () => expect(formatFileSize(2 * 1024 * 1024 * 1024)).toBe('2.00 GB'))
})

describe('formatDuration', () => {
  it('formats minutes', () => expect(formatDuration(754)).toBe('12:34'))
  it('formats hours', () => expect(formatDuration(3754)).toBe('1:02:34'))
  it('formats zero', () => expect(formatDuration(0)).toBe('0:00'))
  it('formats exactly one hour', () => expect(formatDuration(3600)).toBe('1:00:00'))
})

describe('detectUploadType', () => {
  const file = (name: string) => new File([''], name)
  it('detects transcription', () => expect(detectUploadType([file('video.mp4')])).toBe('transcribe'))
  it('detects combine', () => expect(detectUploadType([file('video.mp4'), file('subs.srt')])).toBe('combine'))
  it('detects SRT edit', () => expect(detectUploadType([file('subs.srt')])).toBe('edit-srt'))
  it('detects unknown', () => expect(detectUploadType([file('readme.txt')])).toBe('unknown'))
  it('detects audio', () => expect(detectUploadType([file('podcast.mp3')])).toBe('transcribe'))
  it('detects uppercase extensions', () => expect(detectUploadType([file('VIDEO.MP4')])).toBe('transcribe'))
  it('detects two media files as transcribe', () => expect(detectUploadType([file('a.mp4'), file('b.mp4')])).toBe('transcribe'))
})

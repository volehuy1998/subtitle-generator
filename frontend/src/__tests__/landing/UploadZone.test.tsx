import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UploadZone } from '../../components/landing/UploadZone'

describe('UploadZone', () => {
  it('renders drop zone text', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/drop your file/i)).toBeDefined()
  })

  it('shows supported formats', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/mp4.*mkv.*wav.*mp3/i)).toBeDefined()
  })

  it('shows size limit', () => {
    render(<UploadZone onUpload={() => {}} />)
    expect(screen.getByText(/2gb/i)).toBeDefined()
  })
})

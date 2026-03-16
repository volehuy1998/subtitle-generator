import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'
import { useTaskQueue } from '../useTaskQueue'
import type { TasksResponse } from '@/api/types'

const MOCK_TASKS: TasksResponse = {
  tasks: [
    { task_id: 'task-1', status: 'done', filename: 'audio.mp3', percent: 100 },
    { task_id: 'task-2', status: 'transcribing', filename: 'video.mp4', percent: 45 },
  ],
}

describe('useTaskQueue', () => {
  afterEach(() => {
    server.resetHandlers()
  })

  // ── open=false ────────────────────────────────────────────────────────────

  it('returns empty array when open is false', () => {
    const { result } = renderHook(() => useTaskQueue(false))
    expect(result.current).toEqual([])
  })

  // ── open=true fetches tasks ───────────────────────────────────────────────

  it('fetches and returns task list when open is true', async () => {
    server.use(
      http.get('/tasks', () => HttpResponse.json<TasksResponse>(MOCK_TASKS))
    )

    const { result } = renderHook(() => useTaskQueue(true))

    await waitFor(() => {
      expect(result.current).toHaveLength(2)
    })

    expect(result.current[0].task_id).toBe('task-1')
    expect(result.current[1].task_id).toBe('task-2')
  })

  // ── Polling ───────────────────────────────────────────────────────────────

  it('polls again after interval', async () => {
    let callCount = 0
    server.use(
      http.get('/tasks', () => {
        callCount++
        return HttpResponse.json<TasksResponse>(MOCK_TASKS)
      })
    )

    renderHook(() => useTaskQueue(true))

    // Wait for initial fetch
    await waitFor(() => {
      expect(callCount).toBeGreaterThanOrEqual(1)
    })

    // Wait for at least one polling cycle (2s interval)
    await waitFor(() => {
      expect(callCount).toBeGreaterThanOrEqual(2)
    }, { timeout: 5000 })
  })

  // ── open transition to false clears interval ──────────────────────────────

  it('clears interval when open transitions to false', async () => {
    let callCount = 0
    server.use(
      http.get('/tasks', () => {
        callCount++
        return HttpResponse.json<TasksResponse>(MOCK_TASKS)
      })
    )

    const { rerender } = renderHook(
      ({ open }) => useTaskQueue(open),
      { initialProps: { open: true } }
    )

    // Wait for initial fetch
    await waitFor(() => {
      expect(callCount).toBeGreaterThanOrEqual(1)
    })

    const countAfterOpen = callCount

    // Close the queue
    act(() => {
      rerender({ open: false })
    })

    // Wait a bit to confirm no more fetches happen
    await new Promise(r => setTimeout(r, 100))
    expect(callCount).toBe(countAfterOpen)
  })

  // ── API error returns empty array ─────────────────────────────────────────

  it('returns empty array on API error', async () => {
    server.use(
      http.get('/tasks', () => new HttpResponse(null, { status: 500 }))
    )

    const { result } = renderHook(() => useTaskQueue(true))

    // Wait for the fetch to complete (it will error and catch)
    await new Promise(r => setTimeout(r, 100))

    // Should gracefully handle error and return empty array
    expect(result.current).toEqual([])
  })
})

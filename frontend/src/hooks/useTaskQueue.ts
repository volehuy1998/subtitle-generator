import { useEffect, useState } from 'react'
import { api } from '@/api/client'
import type { TaskListItem } from '@/api/types'

export function useTaskQueue(open: boolean) {
  const [tasks, setTasks] = useState<TaskListItem[]>([])

  useEffect(() => {
    if (!open) return
    const load = () => api.tasks().then(r => setTasks(r.tasks)).catch(() => {})
    load()
    const id = setInterval(load, 2000)
    return () => clearInterval(id)
  }, [open])

  return tasks
}

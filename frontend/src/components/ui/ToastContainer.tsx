import { useToastStore } from '../../store/toastStore'
import { Toast } from './Toast'

export function ToastContainer() {
  const toasts = useToastStore(s => s.toasts)
  const removeToast = useToastStore(s => s.removeToast)

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2"
      aria-label="Notifications"
    >
      {toasts.map(t => (
        <Toast key={t.id} toast={t} onDismiss={removeToast} />
      ))}
    </div>
  )
}

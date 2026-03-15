/**
 * Phase Lumen — Process liveness indicator.
 *
 * Shows users whether the system is actively processing or frozen:
 * - Green pulsing dot + "Live (Xs ago)" when receiving SSE events
 * - Yellow warning after 30s without update
 * - Red "Connection lost" if SSE disconnects
 *
 * Pixel (Sr. Frontend Engineer) — Sprint L5
 */

import { useSyncExternalStore } from 'react';
import { useTaskStore } from '@/store/taskStore';

// Subscribe to a 1-second clock tick without impure render calls
let clockListeners: Array<() => void> = [];
let clockSnapshot = 0;
setInterval(() => {
  clockSnapshot = Date.now();
  clockListeners.forEach((fn) => fn());
}, 1000);
function subscribeClock(cb: () => void) {
  clockListeners.push(cb);
  return () => { clockListeners = clockListeners.filter((fn) => fn !== cb); };
}
function getClockSnapshot() { return clockSnapshot; }

export function LivenessIndicator() {
  const { status, lastEventTime } = useTaskStore();
  const now = useSyncExternalStore(subscribeClock, getClockSnapshot);

  // Don't show when task is complete/cancelled/error
  const isActive = status === 'uploading' || status === 'queued' || status === 'transcribing' ||
    status === 'extracting' || status === 'loading_model' || status === 'probing';

  if (!isActive) return null;

  const lastEvent = lastEventTime || now;
  const secondsAgo = Math.floor((now - lastEvent) / 1000);

  let dotColor: string;
  let label: string;
  let animation: string;

  if (secondsAgo < 15) {
    dotColor = 'var(--color-success)';
    label = secondsAgo <= 1 ? 'Live' : `Live (${secondsAgo}s ago)`;
    animation = 'pulse 2s ease-in-out infinite';
  } else if (secondsAgo < 60) {
    dotColor = 'var(--color-warning)';
    label = `Slow (${secondsAgo}s ago)`;
    animation = 'none';
  } else {
    dotColor = 'var(--color-danger)';
    label = `No response (${secondsAgo}s)`;
    animation = 'none';
  }

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '12px',
        color: 'var(--color-text-3)',
        fontFamily: 'var(--font-family-mono)',
      }}
      aria-live="polite"
      title={`Last SSE event: ${secondsAgo}s ago`}
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: dotColor,
          display: 'inline-block',
          animation,
        }}
      />
      {label}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}

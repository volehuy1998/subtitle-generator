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

import { useEffect, useState } from 'react';
import { useTaskStore } from '@/store/taskStore';

export function LivenessIndicator() {
  const { status, lastEventTime } = useTaskStore();
  const [now, setNow] = useState(Date.now());

  // Update "now" every second to keep the time-since-update ticking
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Don't show when task is complete/cancelled/error
  const isActive = status === 'uploading' || status === 'queued' || status === 'transcribing' ||
    status === 'extracting' || status === 'loading_model' || status === 'probing';

  if (!isActive) return null;

  const lastEvent = lastEventTime || Date.now();
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

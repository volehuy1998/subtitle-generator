/**
 * Phase Lumen — User confirmation before transcription.
 *
 * Shows a summary of the selected options and requires explicit
 * user confirmation before starting the process. No action starts
 * without consent.
 *
 * Pixel (Sr. Frontend Engineer) — Sprint L4
 * Speed estimates added — Sprint L12
 */

/** Approximate speed factors (realtime multiplier) per model/device combo */
const SPEED_ESTIMATES: Record<string, Record<string, number>> = {
  cpu: { tiny: 6, base: 4, small: 2, medium: 0.8, large: 0.3 },
  cuda: { tiny: 30, base: 20, small: 10, medium: 5, large: 2 },
};

function formatSpeedEstimate(device: string, model: string): string | null {
  const deviceKey = device === 'cuda' ? 'cuda' : 'cpu';
  const factor = SPEED_ESTIMATES[deviceKey]?.[model];
  if (factor == null) return null;
  const label = device === 'cuda' ? 'GPU' : 'CPU';
  const modelLabel = model.charAt(0).toUpperCase() + model.slice(1);
  if (factor >= 1) {
    return `~${factor}x realtime (${label}, ${modelLabel})`;
  }
  return `~${factor}x realtime (${label}, ${modelLabel}) — slower than realtime`;
}

interface ConfirmationDialogProps {
  file: File;
  model: string;
  language: string;
  format: string;
  translateTo?: string;
  device: string;
  onConfirm: () => void;
  onCancel: () => void;
  /** True when the selected model is not yet loaded in memory */
  modelNotLoaded?: boolean;
  /** Name of a ready model that the user can switch to */
  readyModelName?: string;
  /** Called when user opts to switch to the ready model */
  onSwitchModel?: (model: string) => void;
}

const MODEL_LABELS: Record<string, string> = {
  tiny: 'Tiny (75 MB)',
  base: 'Base (140 MB)',
  small: 'Small (460 MB)',
  medium: 'Medium (1.5 GB)',
  large: 'Large (3 GB)',
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function ConfirmationDialog({
  file,
  model,
  language,
  format,
  translateTo,
  device,
  onConfirm,
  onCancel,
  modelNotLoaded,
  readyModelName,
  onSwitchModel,
}: ConfirmationDialogProps) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        zIndex: 50,
      }}
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-label="Confirm transcription"
    >
      <div
        style={{
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px',
          maxWidth: '480px',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3
          style={{
            margin: '0 0 8px 0',
            fontSize: '20px',
            fontWeight: 600,
            color: 'var(--color-text)',
          }}
        >
          Ready to transcribe
        </h3>

        <p
          style={{
            margin: '0 0 24px 0',
            fontSize: '14px',
            color: 'var(--color-text-2)',
          }}
        >
          Please confirm the settings below before starting.
        </p>

        <div
          style={{
            background: 'var(--color-surface)',
            borderRadius: 'var(--radius)',
            padding: '16px',
            marginBottom: '24px',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <tbody>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)', width: '100px' }}>File</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)', fontWeight: 500 }}>
                  {file.name}
                  <span style={{ color: 'var(--color-text-3)', marginLeft: '8px' }}>
                    ({formatFileSize(file.size)})
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Model</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>
                  {MODEL_LABELS[model] || model}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Language</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>
                  {language === '' || language === 'auto' ? 'Auto-detect' : language}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Format</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)', textTransform: 'uppercase' }}>
                  {format}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Device</td>
                <td style={{ padding: '6px 0', color: 'var(--color-text)', textTransform: 'uppercase' }}>
                  {device}
                </td>
              </tr>
              {translateTo && (
                <tr>
                  <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Translate</td>
                  <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>{translateTo}</td>
                </tr>
              )}
              {formatSpeedEstimate(device, model) && (
                <tr>
                  <td style={{ padding: '6px 0', color: 'var(--color-text-3)' }}>Processing speed</td>
                  <td style={{ padding: '6px 0', color: 'var(--color-text)' }}>
                    {formatSpeedEstimate(device, model)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Model load warning — shown when selected model is not loaded */}
        {modelNotLoaded && (
          <div
            style={{
              background: 'var(--color-warning-light)',
              border: '1px solid #FDE68A',
              borderRadius: 'var(--radius)',
              padding: '12px 16px',
              marginBottom: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M8 1.5l6.5 12H1.5L8 1.5z" stroke="#D97706" strokeWidth="1.3" strokeLinejoin="round" fill="none" />
                <path d="M8 6.5v3" stroke="#D97706" strokeWidth="1.3" strokeLinecap="round" />
                <circle cx="8" cy="11.5" r="0.6" fill="#D97706" />
              </svg>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'var(--color-text)',
                }}
              >
                The <strong>{model}</strong> model is not loaded yet. Loading may take 30–60 seconds.
              </span>
            </div>
            {readyModelName && onSwitchModel && (
              <button
                type="button"
                onClick={() => onSwitchModel(readyModelName)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'var(--color-primary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  textDecoration: 'underline',
                  textUnderlineOffset: '2px',
                }}
              >
                Use {readyModelName.charAt(0).toUpperCase() + readyModelName.slice(1)} instead (ready)
              </button>
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg)',
              color: 'var(--color-text-2)',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '10px 24px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: 'var(--color-primary)',
              color: 'white',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            {modelNotLoaded ? 'Load & Transcribe' : 'Start Transcription'}
          </button>
        </div>
      </div>
    </div>
  );
}

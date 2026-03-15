/**
 * Phase Lumen — User confirmation before transcription.
 *
 * Shows a summary of the selected options and requires explicit
 * user confirmation before starting the process. No action starts
 * without consent.
 *
 * Pixel (Sr. Frontend Engineer) — Sprint L4
 */

interface ConfirmationDialogProps {
  file: File;
  model: string;
  language: string;
  format: string;
  translateTo?: string;
  device: string;
  onConfirm: () => void;
  onCancel: () => void;
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
            </tbody>
          </table>
        </div>

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
            Start Transcription
          </button>
        </div>
      </div>
    </div>
  );
}

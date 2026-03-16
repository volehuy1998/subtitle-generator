import type { StepTimings } from '@/api/types'

interface Props {
  activeStep: number
  stepTimings: StepTimings
  isPaused: boolean
  isUploading?: boolean
  uploadPercent?: number
}

const BASE_STEPS = [
  { label: 'Upload', key: 'upload' as keyof StepTimings },
  { label: 'Extract', key: 'extract' as keyof StepTimings },
  { label: 'Transcribe', key: 'transcribe' as keyof StepTimings },
]

const TRANSLATE_STEP = { label: 'Translate', key: 'translate' as keyof StepTimings }
const DONE_STEP = { label: 'Done', key: 'finalize' as keyof StepTimings }

function formatTiming(sec: number | undefined): string {
  if (sec === undefined || sec === null) return ''
  if (sec < 60) return `${sec.toFixed(1)}s`
  return `${Math.floor(sec / 60)}m ${(sec % 60).toFixed(0)}s`
}

export function PipelineSteps({ activeStep, stepTimings, isPaused, isUploading, uploadPercent }: Props) {
  // Include Translate step only when translation timing is present
  const hasTranslation = stepTimings.translate !== undefined
  const STEPS = hasTranslation
    ? [...BASE_STEPS, TRANSLATE_STEP, DONE_STEP]
    : [...BASE_STEPS, DONE_STEP]

  // Count completed steps for progressbar
  const effectiveStepForCount = isUploading ? 0 : activeStep
  const completedSteps = Math.min(effectiveStepForCount, STEPS.length)

  return (
    <div
      className="flex items-start w-full"
      role="progressbar"
      aria-valuenow={completedSteps}
      aria-valuemax={STEPS.length}
      aria-label="Pipeline progress"
    >
      {STEPS.map((step, index) => {
        // During upload phase, show Upload step (index 0) as active
        const effectiveStep = isUploading ? 0 : activeStep
        const isDone = effectiveStep > index
        const isActive = effectiveStep === index
        const timing = stepTimings[step.key]

        const circleColor =
          isDone ? 'var(--color-success)' :
          isActive && isPaused ? 'var(--color-warning)' :
          isActive ? 'var(--color-primary)' :
          'transparent'

        const circleBorder =
          isDone ? 'var(--color-success)' :
          isActive && isPaused ? 'var(--color-warning)' :
          isActive ? 'var(--color-primary)' :
          'var(--color-border-2)'

        const textColor =
          isDone ? 'var(--color-success)' :
          isActive ? 'var(--color-primary)' :
          'var(--color-text-3)'

        const numberColor =
          isDone || isActive ? 'white' : 'var(--color-text-3)'

        return (
          <div key={step.label} className="flex items-start flex-1">
            {/* Step node */}
            <div className="flex flex-col items-center gap-1.5 flex-1">
              {/* Circle */}
              <div
                className="flex items-center justify-center w-7 h-7 rounded-full border-2 transition-all duration-300"
                aria-label={`Step ${index + 1}: ${step.label} — ${isDone ? 'complete' : isActive ? 'in progress' : 'pending'}`}
                style={{
                  background: circleColor,
                  borderColor: circleBorder,
                  animation: isActive && !isPaused ? 'stepPulse 2s ease-in-out infinite' : 'none',
                }}
              >
                {isDone ? (
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <path
                      d="M2 6l3 3 5-5"
                      stroke="white"
                      strokeWidth="1.75"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <span
                    className="text-xs font-semibold"
                    style={{ color: numberColor }}
                  >
                    {index + 1}
                  </span>
                )}
              </div>

              {/* Label */}
              <span
                className="text-xs font-medium transition-colors duration-200"
                style={{ color: textColor }}
              >
                {step.label}
              </span>

              {/* Timing / Upload percent */}
              <span
                className="text-xs"
                style={{
                  color: isUploading && index === 0 ? 'var(--color-primary)' : 'var(--color-text-3)',
                  minHeight: '16px',
                  fontSize: '11px',
                  fontWeight: isUploading && index === 0 ? 500 : 'normal',
                }}
              >
                {isUploading && index === 0 ? `${uploadPercent ?? 0}%` : formatTiming(timing)}
              </span>
            </div>

            {/* Connector line (not after last step) */}
            {index < STEPS.length - 1 && (
              <div
                className="flex-1 h-0.5 mt-3.5 transition-all duration-500"
                style={{
                  background: isDone ? 'var(--color-success)' : 'var(--color-border)',
                  maxWidth: '100%',
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

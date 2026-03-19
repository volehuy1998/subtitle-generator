import { Slider } from '../ui/Slider'
import { ColorPicker } from '../ui/ColorPicker'
import { Switch } from '../ui/Switch'
import { Select } from '../ui/Select'

export interface EmbedStyle {
  fontName: string
  fontSize: number
  fontColor: string
  bold: boolean
  position: 'top' | 'center' | 'bottom'
  backgroundOpacity: number
}

interface Props {
  style: EmbedStyle
  onChange: (style: EmbedStyle) => void
}

const POSITION_OPTIONS = [
  { value: 'top', label: 'Top' },
  { value: 'center', label: 'Center' },
  { value: 'bottom', label: 'Bottom' },
]

export function CustomEmbedStyler({ style, onChange }: Props) {
  const update = <K extends keyof EmbedStyle>(key: K, value: EmbedStyle[K]) =>
    onChange({ ...style, [key]: value })

  return (
    <div className="space-y-4 pt-3 border-t border-[var(--color-border)]">
      <p className="text-sm font-medium text-[var(--color-text)]">Custom style</p>
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-[var(--color-text)]">Font name</label>
        <input
          type="text"
          value={style.fontName}
          onChange={(e) => update('fontName', e.target.value)}
          className="w-full h-9 px-3 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md text-[var(--color-text)] focus:outline-none focus:border-[var(--color-border-focus)] focus:ring-1 focus:ring-[var(--color-border-focus)] transition-colors"
          placeholder="Arial"
        />
      </div>
      <Slider label="Font size" value={style.fontSize} onChange={(v) => update('fontSize', v)} min={8} max={72} unit="pt" />
      <ColorPicker label="Font color" value={style.fontColor} onChange={(v) => update('fontColor', v)} />
      <Switch checked={style.bold} onChange={(v) => update('bold', v)} label="Bold" />
      <Select
        label="Position"
        value={style.position}
        onChange={(e) => update('position', e.target.value as EmbedStyle['position'])}
        options={POSITION_OPTIONS}
      />
      <Slider label="Background opacity" value={style.backgroundOpacity} onChange={(v) => update('backgroundOpacity', v)} min={0} max={1} step={0.1} />
    </div>
  )
}

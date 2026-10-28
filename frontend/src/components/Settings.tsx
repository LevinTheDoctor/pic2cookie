import { useEffect, useRef, useState } from 'react'
import type { CoasterParams, Design, DesignPatch, CutterParams, FilamentParams, Meta, TraceParams } from '../api'
import { useI18n, type Key } from '../i18n'

type Num<T> = { [K in keyof T]: T[K] extends number ? K : never }[keyof T]

interface NumberSpec<T> {
  key: Num<T>
  label: Key
  min: number
  max: number
  step: number
  unit?: string
}

const MAIN: NumberSpec<CutterParams>[] = [
  { key: 'size', label: 'cutter.size', min: 20, max: 250, step: 1, unit: 'mm' },
  { key: 'blade_height', label: 'cutter.blade_height', min: 6, max: 40, step: 0.5, unit: 'mm' },
  { key: 'blade_thickness', label: 'cutter.blade_thickness', min: 0.4, max: 2.4, step: 0.05, unit: 'mm' },
  { key: 'flange_width', label: 'cutter.flange_width', min: 0, max: 12, step: 0.5, unit: 'mm' },
]

const MORE: NumberSpec<CutterParams>[] = [
  { key: 'flange_height', label: 'cutter.flange_height', min: 0.6, max: 6, step: 0.2, unit: 'mm' },
  { key: 'imprint_offset', label: 'cutter.imprint_offset', min: 0.5, max: 15, step: 0.5, unit: 'mm' },
  { key: 'imprint_thickness', label: 'cutter.imprint_thickness', min: 0.4, max: 2.4, step: 0.05, unit: 'mm' },
  { key: 'bridge_width', label: 'cutter.bridge_width', min: 1, max: 10, step: 0.5, unit: 'mm' },
  { key: 'min_hole', label: 'cutter.min_hole', min: 0, max: 30, step: 0.5, unit: 'mm' },
  { key: 'min_imprint', label: 'cutter.min_imprint', min: 0, max: 10, step: 0.5, unit: 'mm' },
]

const COASTER: NumberSpec<CoasterParams>[] = [
  { key: 'size', label: 'coaster.size', min: 40, max: 250, step: 1, unit: 'mm' },
  { key: 'thickness', label: 'coaster.thickness', min: 2, max: 10, step: 0.2, unit: 'mm' },
  { key: 'margin', label: 'coaster.margin', min: 0, max: 40, step: 0.5, unit: 'mm' },
]

const COASTER_MORE: NumberSpec<CoasterParams>[] = [
  { key: 'motif_depth', label: 'coaster.motif_depth', min: 0.2, max: 3, step: 0.2, unit: 'mm' },
  { key: 'min_line', label: 'coaster.min_line', min: 0, max: 2, step: 0.05, unit: 'mm' },
  { key: 'rim_width', label: 'coaster.rim_width', min: 1, max: 10, step: 0.5, unit: 'mm' },
  { key: 'rim_height', label: 'coaster.rim_height', min: 0.2, max: 4, step: 0.2, unit: 'mm' },
  { key: 'foot_diameter', label: 'coaster.foot_diameter', min: 4, max: 25, step: 0.5, unit: 'mm' },
  { key: 'foot_depth', label: 'coaster.foot_depth', min: 0.4, max: 3, step: 0.2, unit: 'mm' },
  { key: 'opener_thickness', label: 'coaster.opener_thickness', min: 4, max: 12, step: 0.2, unit: 'mm' },
]

const COINS: CoasterParams['coin'][] = ['eur2', 'eur1', 'eur050', 'usd025', 'custom']

const TRACE: NumberSpec<TraceParams>[] = [
  { key: 'tolerance', label: 'trace.tolerance', min: 0, max: 1, step: 0.01 },
  { key: 'smoothing', label: 'trace.smoothing', min: 0, max: 6, step: 0.1, unit: 'px' },
]

function NumberField<T>({
  spec,
  value,
  onChange,
}: {
  spec: NumberSpec<T>
  value: number
  onChange: (v: number) => void
}) {
  const { t } = useI18n()
  const id = `f-${String(spec.key)}`
  return (
    <div className="field">
      <label htmlFor={id}>{t(spec.label)}</label>
      <span className="value">
        <input
          type="number"
          aria-label={t(spec.label)}
          min={spec.min}
          max={spec.max}
          step={spec.step}
          value={value}
          onChange={(e) => e.target.value !== '' && onChange(Number(e.target.value))}
        />
        {spec.unit}
      </span>
      <input
        id={id}
        type="range"
        min={spec.min}
        max={spec.max}
        step={spec.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  )
}

function Segmented<V extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly (readonly [V, string])[]
  value: V
  onChange: (v: V) => void
}) {
  return (
    <span className="segmented">
      {options.map(([v, label]) => (
        <button key={v} type="button" className={v === value ? 'on' : ''} onClick={() => onChange(v)}>
          {label}
        </button>
      ))}
    </span>
  )
}

/** Holds edits locally and sends them after a short pause, so sliders stay smooth. */
function useDebounced<T>(value: T, send: (v: T) => void, delay = 450) {
  const [draft, setDraft] = useState(value)
  const timer = useRef<number>(undefined)
  const sendRef = useRef(send)
  useEffect(() => {
    sendRef.current = send
  })
  // Follow the server's value, unless an edit is still waiting to be sent.
  const key = JSON.stringify(value)
  useEffect(() => {
    if (timer.current === undefined) setDraft(JSON.parse(key))
  }, [key])
  useEffect(() => () => window.clearTimeout(timer.current), [])
  const update = (next: T) => {
    setDraft(next)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      timer.current = undefined
      sendRef.current(next)
    }, delay)
  }
  return [draft, update] as const
}

export function CutterSettings({
  design,
  onPatch,
}: {
  design: Design
  onPatch: (patch: DesignPatch) => void
}) {
  const { t } = useI18n()
  const [cutter, setCutter] = useDebounced(design.cutter, (cutter) => onPatch({ cutter }))
  const set = <K extends keyof CutterParams>(key: K, value: CutterParams[K]) =>
    setCutter({ ...cutter, [key]: value })
  return (
    <div className="card">
      <h2>{t('cutter.title')}</h2>
      <div className="fields">
        {MAIN.map((spec) => (
          <NumberField key={spec.key} spec={spec} value={cutter[spec.key]} onChange={(v) => set(spec.key, v)} />
        ))}
        <div className="field">
          <label>{t('cutter.support')}</label>
          <Segmented
            options={[
              ['bridges', t('cutter.bridges')],
              ['plate', t('cutter.plate')],
            ]}
            value={cutter.support}
            onChange={(v) => set('support', v)}
          />
        </div>
        <details className="more">
          <summary>{t('settings.more')}</summary>
          <div className="fields">
            {MORE.map((spec) => (
              <NumberField key={spec.key} spec={spec} value={cutter[spec.key]} onChange={(v) => set(spec.key, v)} />
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}

function Check({
  id,
  label,
  checked,
  onChange,
}: {
  id: string
  label: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </div>
  )
}

function Colour({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input
        type="color"
        aria-label={label}
        className="control"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: 40, height: 30, padding: 2 }}
      />
    </div>
  )
}

export function CoasterSettings({
  design,
  onPatch,
}: {
  design: Design
  onPatch: (patch: DesignPatch) => void
}) {
  const { t } = useI18n()
  const [coaster, setCoaster] = useDebounced(design.coaster, (coaster) => onPatch({ coaster }))
  const set = <K extends keyof CoasterParams>(key: K, value: CoasterParams[K]) =>
    setCoaster({ ...coaster, [key]: value })
  const number = (spec: NumberSpec<CoasterParams>) => (
    <NumberField key={spec.key} spec={spec} value={coaster[spec.key]} onChange={(v) => set(spec.key, v)} />
  )
  const silhouette = coaster.shape === 'silhouette'
  return (
    <div className="card">
      <h2>{t('coaster.title')}</h2>
      <div className="fields">
        <div className="field">
          <label>{t('coaster.shape')}</label>
          <Segmented
            options={(['round', 'square', 'rounded', 'silhouette'] as const).map((v) => [v, t(`coaster.${v}`)] as const)}
            value={coaster.shape}
            onChange={(v) => set('shape', v)}
          />
        </div>
        {COASTER.map(number)}
        {coaster.shape === 'rounded' &&
          number({ key: 'corner_radius', label: 'coaster.corner_radius', min: 0, max: 50, step: 0.5, unit: 'mm' })}
        {!silhouette &&
          number({ key: 'motif_scale', label: 'coaster.motif_scale', min: 0.1, max: 1, step: 0.01 })}
        <div className="field">
          <label>{t('coaster.motif')}</label>
          <Segmented
            options={(['inlay', 'raised', 'engraved'] as const).map((v) => [v, t(`coaster.${v}`)] as const)}
            value={coaster.motif_style}
            onChange={(v) => set('motif_style', v)}
          />
        </div>
        <Check id="f-invert-motif" label={t('coaster.invert')} checked={coaster.invert} onChange={(v) => set('invert', v)} />
        <Colour label={t('coaster.plate_colour')} value={coaster.plate_colour} onChange={(v) => set('plate_colour', v)} />
        {coaster.motif_style !== 'engraved' && (
          <Colour label={t('coaster.motif_colour')} value={coaster.motif_colour} onChange={(v) => set('motif_colour', v)} />
        )}
        <Check id="f-rim" label={t('coaster.rim')} checked={coaster.rim} onChange={(v) => set('rim', v)} />
        <Check id="f-feet" label={t('coaster.feet')} checked={coaster.feet} onChange={(v) => set('feet', v)} />
        <div className="field">
          <label htmlFor="f-opener">{t('coaster.opener')}</label>
          <select id="f-opener" value={coaster.opener} onChange={(e) => set('opener', e.target.value as CoasterParams['opener'])}>
            {(['none', 'coin', 'plastic'] as const).map((v) => (
              <option key={v} value={v}>
                {t(`coaster.opener.${v}`)}
              </option>
            ))}
          </select>
        </div>
        {coaster.opener !== 'none' && (
          <div className="field">
            <label>{t('coaster.opener_side')}</label>
            <Segmented
              options={(['left', 'top', 'bottom', 'right'] as const).map((v) => [v, t(`coaster.${v}`)] as const)}
              value={coaster.opener_side}
              onChange={(v) => set('opener_side', v)}
            />
          </div>
        )}
        {coaster.opener === 'coin' && (
          <div className="field">
            <label htmlFor="f-coin">{t('coaster.coin')}</label>
            <select id="f-coin" value={coaster.coin} onChange={(e) => set('coin', e.target.value as CoasterParams['coin'])}>
              {COINS.map((v) => (
                <option key={v} value={v}>
                  {t(`coaster.coin.${v}`)}
                </option>
              ))}
            </select>
          </div>
        )}
        {coaster.opener === 'coin' &&
          coaster.coin === 'custom' && [
            number({ key: 'coin_diameter', label: 'coaster.coin_diameter', min: 15, max: 40, step: 0.05, unit: 'mm' }),
            number({ key: 'coin_thickness', label: 'coaster.coin_thickness', min: 1, max: 4, step: 0.05, unit: 'mm' }),
          ]}
        <details className="more">
          <summary>{t('settings.more')}</summary>
          <div className="fields">{COASTER_MORE.map(number)}</div>
        </details>
      </div>
    </div>
  )
}

export function TraceSettings({
  design,
  onPatch,
}: {
  design: Design
  onPatch: (patch: DesignPatch) => void
}) {
  const { t } = useI18n()
  const [trace, setTrace] = useDebounced(design.trace, (trace) => onPatch({ trace }))
  const set = <K extends keyof TraceParams>(key: K, value: TraceParams[K]) => setTrace({ ...trace, [key]: value })
  const alpha = trace.ink === 'alpha'
  return (
    <div className="card">
      <h2>
        {t('trace.title')} <span className="hint">{t('trace.hint')}</span>
      </h2>
      <div className="fields">
        <div className="field">
          <label>{t('trace.ink')}</label>
          <span className="value">
            <Segmented
              options={[
                ['colour', t('trace.colour')],
                ['alpha', t('trace.alpha')],
              ]}
              value={alpha ? 'alpha' : 'colour'}
              onChange={(v) => set('ink', v === 'alpha' ? 'alpha' : '#000000')}
            />
            {!alpha && (
              <input
                type="color"
                aria-label={t('trace.inkColour')}
                className="control"
                value={trace.ink}
                onChange={(e) => set('ink', e.target.value)}
                style={{ width: 40, height: 30, padding: 2 }}
              />
            )}
          </span>
        </div>
        {TRACE.map((spec) => (
          <NumberField key={spec.key} spec={spec} value={trace[spec.key]} onChange={(v) => set(spec.key, v)} />
        ))}
        <div className="field">
          <label htmlFor="f-invert">{t('trace.invert')}</label>
          <input id="f-invert" type="checkbox" checked={trace.invert} onChange={(e) => set('invert', e.target.checked)} />
        </div>
      </div>
    </div>
  )
}

export function PrintSettings({
  design,
  meta,
  onPatch,
}: {
  design: Design
  meta: Meta
  onPatch: (patch: DesignPatch) => void
}) {
  const { t } = useI18n()
  const [filament, setFilament] = useDebounced<FilamentParams>(design.filament, (filament) => onPatch({ filament }))
  const printer = meta.printers.find((p) => p.id === design.printer) ?? meta.printers[0]
  return (
    <div className="fields">
      <div className="field">
        <label htmlFor="f-printer">{t('print.printer')}</label>
        <select
          id="f-printer"
          value={design.printer}
          onChange={(e) => {
            const next = meta.printers.find((p) => p.id === e.target.value)!
            const patch: DesignPatch = { printer: next.id }
            if (!next.materials.includes(filament.material)) patch.filament = { ...filament, material: 'pla' }
            onPatch(patch)
          }}
        >
          {meta.printers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="f-material">{t('print.material')}</label>
        <select
          id="f-material"
          value={filament.material}
          onChange={(e) => setFilament({ ...filament, material: e.target.value as FilamentParams['material'] })}
        >
          {printer.materials.map((m) => (
            <option key={m} value={m}>
              {m.toUpperCase()}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="f-price">{t('print.price')}</label>
        <span className="value">
          <input
            id="f-price"
            type="number"
            min={0}
            step={0.5}
            placeholder="–"
            value={filament.price_per_kg ?? ''}
            onChange={(e) =>
              setFilament({ ...filament, price_per_kg: e.target.value === '' ? null : Number(e.target.value) })
            }
          />
        </span>
      </div>
    </div>
  )
}

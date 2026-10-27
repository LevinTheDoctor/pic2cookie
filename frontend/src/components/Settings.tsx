import { useEffect, useRef, useState } from 'react'
import type { CutterParams, Design, DesignPatch, FilamentParams, Meta, TraceParams } from '../api'

type Num<T> = { [K in keyof T]: T[K] extends number ? K : never }[keyof T]

interface NumberSpec<T> {
  key: Num<T>
  label: string
  min: number
  max: number
  step: number
  unit?: string
}

const MAIN: NumberSpec<CutterParams>[] = [
  { key: 'size', label: 'Size (longest side)', min: 20, max: 250, step: 1, unit: 'mm' },
  { key: 'blade_height', label: 'Blade height', min: 6, max: 40, step: 0.5, unit: 'mm' },
  { key: 'blade_thickness', label: 'Blade thickness', min: 0.4, max: 2.4, step: 0.05, unit: 'mm' },
  { key: 'flange_width', label: 'Flange width', min: 0, max: 12, step: 0.5, unit: 'mm' },
]

const MORE: NumberSpec<CutterParams>[] = [
  { key: 'flange_height', label: 'Flange height', min: 0.6, max: 6, step: 0.2, unit: 'mm' },
  { key: 'imprint_offset', label: 'Imprint offset', min: 0.5, max: 15, step: 0.5, unit: 'mm' },
  { key: 'imprint_thickness', label: 'Imprint thickness', min: 0.4, max: 2.4, step: 0.05, unit: 'mm' },
  { key: 'bridge_width', label: 'Bridge width', min: 1, max: 10, step: 0.5, unit: 'mm' },
  { key: 'min_hole', label: 'Smallest hole', min: 0, max: 30, step: 0.5, unit: 'mm' },
  { key: 'min_imprint', label: 'Smallest imprint', min: 0, max: 10, step: 0.5, unit: 'mm' },
]

const TRACE: NumberSpec<TraceParams>[] = [
  { key: 'tolerance', label: 'Colour tolerance', min: 0, max: 1, step: 0.01 },
  { key: 'smoothing', label: 'Smoothing', min: 0, max: 6, step: 0.1, unit: 'px' },
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
  const id = `f-${String(spec.key)}`
  return (
    <div className="field">
      <label htmlFor={id}>{spec.label}</label>
      <span className="value">
        <input
          type="number"
          aria-label={spec.label}
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
  options: [V, string][]
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
  const [cutter, setCutter] = useDebounced(design.cutter, (cutter) => onPatch({ cutter }))
  const set = <K extends keyof CutterParams>(key: K, value: CutterParams[K]) =>
    setCutter({ ...cutter, [key]: value })
  return (
    <div className="card">
      <h2>Cutter</h2>
      <div className="fields">
        {MAIN.map((spec) => (
          <NumberField key={spec.key} spec={spec} value={cutter[spec.key]} onChange={(v) => set(spec.key, v)} />
        ))}
        <div className="field">
          <label>Imprints held by</label>
          <Segmented
            options={[
              ['bridges', 'Bridges'],
              ['plate', 'Back plate'],
            ]}
            value={cutter.support}
            onChange={(v) => set('support', v)}
          />
        </div>
        <details className="more">
          <summary>More settings</summary>
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

export function TraceSettings({
  design,
  onPatch,
}: {
  design: Design
  onPatch: (patch: DesignPatch) => void
}) {
  const [trace, setTrace] = useDebounced(design.trace, (trace) => onPatch({ trace }))
  const set = <K extends keyof TraceParams>(key: K, value: TraceParams[K]) => setTrace({ ...trace, [key]: value })
  const alpha = trace.ink === 'alpha'
  return (
    <div className="card">
      <h2>
        Tracing <span className="hint">changing it resets clicked roles</span>
      </h2>
      <div className="fields">
        <div className="field">
          <label>Ink</label>
          <span className="value">
            <Segmented
              options={[
                ['colour', 'Colour'],
                ['alpha', 'Opaque pixels'],
              ]}
              value={alpha ? 'alpha' : 'colour'}
              onChange={(v) => set('ink', v === 'alpha' ? 'alpha' : '#000000')}
            />
            {!alpha && (
              <input
                type="color"
                aria-label="Ink colour"
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
          <label htmlFor="f-invert">Invert</label>
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
  const [filament, setFilament] = useDebounced<FilamentParams>(design.filament, (filament) => onPatch({ filament }))
  const printer = meta.printers.find((p) => p.id === design.printer) ?? meta.printers[0]
  return (
    <div className="fields">
      <div className="field">
        <label htmlFor="f-printer">Printer</label>
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
        <label htmlFor="f-material">Material</label>
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
        <label htmlFor="f-price">Price per kg</label>
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

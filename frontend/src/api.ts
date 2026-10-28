// Typed client for the Pic2Cookie API (see pic2cookie/api.py).

import type { Notice } from './i18n'

export type Product = 'cutter' | 'coaster'
export type Role = 'outer' | 'hole' | 'imprint' | 'motif' | 'ignore'
export type Material = 'pla' | 'petg' | 'abs'
export type Coin = 'eur2' | 'eur1' | 'eur050' | 'usd025' | 'custom'

export interface CutterParams {
  size: number
  blade_height: number
  blade_thickness: number
  flange_width: number
  flange_height: number
  imprint_offset: number
  imprint_thickness: number
  support: 'bridges' | 'plate'
  bridge_width: number
  min_hole: number
  min_imprint: number
}

export interface CoasterParams {
  shape: 'round' | 'square' | 'rounded' | 'silhouette'
  size: number
  thickness: number
  corner_radius: number
  margin: number
  motif_scale: number
  motif_style: 'inlay' | 'raised' | 'engraved'
  motif_depth: number
  invert: boolean
  min_line: number
  plate_colour: string
  motif_colour: string
  rim: boolean
  rim_width: number
  rim_height: number
  feet: boolean
  foot_diameter: number
  foot_depth: number
  opener: 'none' | 'coin' | 'plastic'
  opener_side: 'right' | 'left' | 'top' | 'bottom'
  opener_thickness: number
  coin: Coin
  coin_diameter: number
  coin_thickness: number
}

export interface TraceParams {
  ink: string
  tolerance: number
  invert: boolean
  smoothing: number
}

export interface FilamentParams {
  material: Material
  price_per_kg: number | null
  diameter: number
}

export interface Feature {
  id: string
  kind: 'region' | 'line'
  role: Role
  default_role: Role
  path: string
  area: number
}

export interface FilamentEstimate {
  material: Material
  volume_cm3: number
  grams: number
  metres: number
  cost: number | null
}

export interface PartEstimate {
  name: string
  colour: string | null
  estimate: FilamentEstimate
}

export interface DesignResult {
  product: Product
  style: string
  outline: string
  features: Feature[]
  warnings: Notice[]
  estimate: FilamentEstimate
  parts: PartEstimate[]
  dimensions: { width: number; depth: number; height: number }
  pause_z: number | null
  generated: string
}

export interface Design {
  id: string
  name: string
  created: string
  updated: string
  source: { filename: string; kind: 'svg' | 'raster'; key: string }
  product: Product
  cutter: CutterParams
  coaster: CoasterParams
  trace: TraceParams
  filament: FilamentParams
  printer: string
  roles: Record<string, Role>
  status: 'new' | 'ready' | 'failed'
  error: Notice | null
  result: DesignResult | null
}

export interface Job {
  id: string
  design_id: string
  status: 'queued' | 'running' | 'done' | 'failed'
  error: string | null
}

export interface Printer {
  id: string
  name: string
  bed: [number, number]
  height: number
  materials: Material[]
}

/** Set only when the server runs as a hosted instance. */
export interface Hosting {
  enabled: true
  repository_url: string
  operator: { name: string | null; address: string | null; email: string | null }
  privacy_url: string | null
  retention_days: number | null
}

export interface Meta {
  version: string
  printers: Printer[]
  default_printer: string
  materials: Record<Material, { density: number }>
  formats: { id: string; filenames: Record<Product, string> }[]
  coins: Record<Exclude<Coin, 'custom'>, { diameter: number; thickness: number }>
  defaults: { cutter: CutterParams; coaster: CoasterParams; trace: TraceParams; filament: FilamentParams }
  limits: { upload_mb: number; max_pixels: number; job_timeout: number }
  hosting: Hosting | null
}

export type DesignPatch = Partial<
  Pick<Design, 'name' | 'product' | 'cutter' | 'coaster' | 'trace' | 'filament' | 'printer' | 'roles'>
>

/** A failed request; `notice` is set when the server said why. */
export class ApiError extends Error {
  notice: Notice | null

  constructor(message: string, notice: Notice | null = null) {
    super(message)
    this.notice = notice
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init)
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    let notice: Notice | null = null
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') message = body.detail
      else if (body.detail?.code) notice = body.detail
    } catch {
      // not JSON
    }
    throw new ApiError(notice?.text ?? message, notice)
  }
  return res.status === 204 ? (undefined as T) : res.json()
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  meta: () => request<Meta>('/meta'),
  designs: () => request<Design[]>('/designs'),
  design: (id: string) => request<Design>(`/designs/${id}`),
  upload: (file: File, product: Product) => {
    const form = new FormData()
    form.append('file', file)
    form.append('product', product)
    return request<{ design: Design; job: Job }>('/designs', { method: 'POST', body: form })
  },
  update: (id: string, patch: DesignPatch) =>
    request<{ design: Design; job: Job | null }>(`/designs/${id}`, json('PATCH', patch)),
  duplicate: (id: string) => request<Design>(`/designs/${id}/duplicate`, { method: 'POST' }),
  remove: (id: string) => request<void>(`/designs/${id}`, { method: 'DELETE' }),
  job: (id: string) => request<Job>(`/jobs/${id}`),
}

export function fileUrl(design: Design, name: string, download = false): string {
  const version = encodeURIComponent(design.result?.generated ?? design.updated)
  return `/api/designs/${design.id}/files/${name}?v=${version}${download ? '&download=true' : ''}`
}

/** Poll a job until it finishes. */
export async function waitForJob(job: Job, signal?: AbortSignal): Promise<Job> {
  let current = job
  for (let delay = 150; current.status === 'queued' || current.status === 'running'; ) {
    await new Promise((r) => setTimeout(r, delay))
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')
    current = await api.job(job.id)
    delay = Math.min(delay * 1.5, 1000)
  }
  return current
}

/** The file names the server writes for a Design's Product. */
export function productFiles(design: Design) {
  const p = design.product
  return {
    stl: p === 'coaster' ? 'coaster.stl.zip' : 'cutter.stl',
    threemf: `${p}.3mf`,
    bambu: `${p}.bambu.3mf`,
    // the preview's meshes, each with its colour
    preview:
      p === 'coaster'
        ? (design.result?.parts ?? []).map((part) => ({ file: `${part.name}.stl`, colour: part.colour }))
        : [{ file: 'cutter.stl', colour: null }],
  }
}

/** Bambu Studio registers bambustudio:// and opens the file it is pointed at. */
export function bambuStudioLink(design: Design): string {
  const url = new URL(fileUrl(design, productFiles(design).bambu), window.location.origin)
  return `bambustudio://open?file=${encodeURIComponent(url.toString())}`
}

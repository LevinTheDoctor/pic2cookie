// Typed client for the Pic2Cookie API (see pic2cookie/api.py).

export type Role = 'outer' | 'hole' | 'imprint' | 'ignore'
export type Material = 'pla' | 'petg' | 'abs'

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

export interface DesignResult {
  style: 'filled' | 'line' | 'marked'
  outline: string
  features: Feature[]
  warnings: string[]
  estimate: FilamentEstimate
  dimensions: { width: number; depth: number; height: number }
  generated: string
}

export interface Design {
  id: string
  name: string
  created: string
  updated: string
  source: { filename: string; kind: 'svg' | 'raster'; key: string }
  cutter: CutterParams
  trace: TraceParams
  filament: FilamentParams
  printer: string
  roles: Record<string, Role>
  status: 'new' | 'ready' | 'failed'
  error: string | null
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

export interface Meta {
  version: string
  printers: Printer[]
  default_printer: string
  materials: Record<Material, { density: number }>
  formats: { id: string; filename: string }[]
  defaults: { cutter: CutterParams; trace: TraceParams; filament: FilamentParams }
  limits: { upload_mb: number; max_pixels: number; job_timeout: number }
}

export type DesignPatch = Partial<
  Pick<Design, 'name' | 'cutter' | 'trace' | 'filament' | 'printer' | 'roles'>
>

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init)
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // not JSON
    }
    throw new Error(message)
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
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
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

/** Bambu Studio registers bambustudio:// and opens the file it is pointed at. */
export function bambuStudioLink(design: Design): string {
  const url = new URL(fileUrl(design, 'cutter.bambu.3mf'), window.location.origin)
  return `bambustudio://open?file=${encodeURIComponent(url.toString())}`
}

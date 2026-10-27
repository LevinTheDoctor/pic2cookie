import {
  ArrowPathIcon,
  CheckCircleIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { api, fileUrl, waitForJob, type Design, type DesignPatch, type Feature, type Meta, type Role } from './api'
import { DesignList } from './components/DesignList'
import { Downloads } from './components/Downloads'
import { Estimate } from './components/Estimate'
import { Legend, RoleView } from './components/RoleView'
import { CutterSettings, PrintSettings, TraceSettings } from './components/Settings'
import { Upload } from './components/Upload'

// three.js is large; load it only once a cutter is shown.
const CutterPreview = lazy(() => import('./components/CutterPreview').then((m) => ({ default: m.CutterPreview })))

const selectedFromHash = () => window.location.hash.replace(/^#\/?/, '') || null

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [designs, setDesigns] = useState<Design[]>([])
  const [selected, setSelected] = useState<string | null>(selectedFromHash)
  const [loaded, setDesign] = useState<Design | null>(null)
  const design = loaded && loaded.id === selected ? loaded : null
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const latest = useRef(0) // only the newest change may update the view

  const refreshList = useCallback(() => api.designs().then(setDesigns).catch(() => {}), [])

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message))
    refreshList()
    const onHash = () => setSelected(selectedFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [refreshList])

  useEffect(() => {
    if (!selected) return
    api
      .design(selected)
      .then(setDesign)
      .catch(() => {
        setDesign(null)
        window.location.hash = ''
      })
  }, [selected])

  const select = (id: string | null) => {
    window.location.hash = id ? `/${id}` : ''
    setSelected(id)
    setError(null)
  }

  /** Run a change that starts a generation job, then show the result. */
  const track = async (start: () => Promise<void>) => {
    const ticket = ++latest.current
    setBusy(true)
    setError(null)
    try {
      await start()
      if (ticket === latest.current) await refreshList()
    } catch (e) {
      if (ticket === latest.current) setError((e as Error).message)
    } finally {
      if (ticket === latest.current) setBusy(false)
    }
  }

  const patch = (changes: DesignPatch) => {
    if (!design) return
    setDesign({ ...design, ...changes } as Design)
    track(async () => {
      const { design: saved, job } = await api.update(design.id, changes)
      if (job) await waitForJob(job)
      const fresh = await api.design(saved.id)
      setDesign((current) => (current?.id === fresh.id ? fresh : current))
    })
  }

  const upload = (file: File) =>
    track(async () => {
      const { design: created, job } = await api.upload(file)
      select(created.id)
      setDesign(created)
      await waitForJob(job)
      setDesign(await api.design(created.id))
    })

  const changeRole = (feature: Feature, role: Role) => {
    if (!design) return
    const roles = { ...design.roles }
    if (role === feature.default_role) delete roles[feature.id]
    else roles[feature.id] = role
    if (design.result) {
      const features = design.result.features.map((f) => (f.id === feature.id ? { ...f, role } : f))
      setDesign({ ...design, roles, result: { ...design.result, features } })
    }
    patch({ roles })
  }

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const confirmDelete = design !== null && confirmDeleteId === design.id

  const remove = async () => {
    if (!design) return
    if (!confirmDelete) {
      setConfirmDeleteId(design.id)
      return
    }
    await api.remove(design.id)
    select(null)
    refreshList()
  }

  const duplicate = async () => {
    if (!design) return
    const copy = await api.duplicate(design.id)
    await refreshList()
    select(copy.id)
  }

  const [flipped, setFlipped] = useState(false)

  return (
    <div className="app">
      <header className="header">
        <img src="/logo.svg" alt="" />
        <h1>
          Pic<span>2</span>Cookie
        </h1>
        {meta && <span className="version">v{meta.version}</span>}
      </header>

      <aside className="sidebar">
        <Upload onFile={upload} />
        <p className="section-title">Designs</p>
        <DesignList designs={designs} selected={selected} onSelect={select} />
      </aside>

      <main className="main">
        {error && (
          <div className="card error">
            <ExclamationTriangleIcon className="icon" /> {error}
          </div>
        )}
        {!design && <Upload onFile={upload} hero />}
        {design && meta && (
          <>
            <div className="title-row">
              <input
                aria-label="Design name"
                defaultValue={design.name}
                key={design.id}
                onBlur={(e) => e.target.value.trim() && e.target.value !== design.name && patch({ name: e.target.value.trim() })}
                onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
              />
              <span className="status">
                {busy || design.status === 'new' ? (
                  <>
                    <ArrowPathIcon className="icon spin" /> Generating…
                  </>
                ) : design.status === 'ready' ? (
                  <>
                    <CheckCircleIcon className="icon" style={{ color: 'var(--green)' }} /> Ready
                  </>
                ) : null}
              </span>
              <button className="btn ghost" title="Duplicate" onClick={duplicate}>
                <DocumentDuplicateIcon className="icon" />
              </button>
              <button className="btn ghost danger" title="Delete" onClick={remove}>
                <TrashIcon className="icon" />
                {confirmDelete && 'Click again to delete'}
              </button>
            </div>

            {design.status === 'failed' && (
              <div className="card error">
                <ExclamationTriangleIcon className="icon" /> {design.error}
              </div>
            )}

            <div className="workspace">
              <div className="side" style={{ minWidth: 0 }}>
                <div className="views">
                  <div className="card">
                    <h2>
                      Picture <span className="hint">click a part to change its role</span>
                    </h2>
                    <div className="stage">
                      {design.result ? (
                        <RoleView outline={design.result.outline} features={design.result.features} onChange={changeRole} />
                      ) : (
                        <div className="overlay">Tracing…</div>
                      )}
                    </div>
                    <Legend />
                  </div>
                  <div className="card">
                    <h2>
                      Cutter
                      <span className="hint">
                        <span className="segmented">
                          <button className={!flipped ? 'on' : ''} onClick={() => setFlipped(false)}>
                            Print view
                          </button>
                          <button className={flipped ? 'on' : ''} onClick={() => setFlipped(true)}>
                            Cutting view
                          </button>
                        </span>
                      </span>
                    </h2>
                    <div className="stage">
                      {design.result ? (
                        <Suspense fallback={<div className="overlay">Loading 3D view…</div>}>
                          <CutterPreview url={fileUrl(design, 'cutter.stl')} flipped={flipped} />
                        </Suspense>
                      ) : (
                        <div className="overlay">Generating…</div>
                      )}
                    </div>
                  </div>
                </div>
                {design.result && design.result.warnings.length > 0 && (
                  <ul className="warnings">
                    {design.result.warnings.map((w) => (
                      <li key={w}>
                        <ExclamationTriangleIcon className="icon" /> {w}
                      </li>
                    ))}
                  </ul>
                )}
                <CutterSettings design={design} onPatch={patch} />
                {design.source.kind === 'raster' && <TraceSettings design={design} onPatch={patch} />}
              </div>

              <div className="side">
                <div className="card">
                  <h2>Filament estimate</h2>
                  {design.result ? <Estimate result={design.result} /> : <p className="note">Generating…</p>}
                  <p className="note">Printed nearly solid; your slicer may differ slightly.</p>
                </div>
                <div className="card">
                  <h2>Print</h2>
                  <PrintSettings design={design} meta={meta} onPatch={patch} />
                </div>
                {design.result && (
                  <div className="card">
                    <h2>Download</h2>
                    <Downloads design={design} />
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

import {
  ArrowPathIcon,
  CheckCircleIcon,
  CodeBracketIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import {
  api,
  ApiError,
  fileUrl,
  productFiles,
  waitForJob,
  type Design,
  type DesignPatch,
  type Feature,
  type Meta,
  type Product,
  type Role,
} from './api'
import { DesignList } from './components/DesignList'
import { Downloads } from './components/Downloads'
import { Estimate } from './components/Estimate'
import { PrivacyDialog, UploadNotice } from './components/Privacy'
import { Legend, RoleView } from './components/RoleView'
import { CoasterSettings, CutterSettings, PrintSettings, TraceSettings } from './components/Settings'
import { ProductChoice, Upload } from './components/Upload'
import { I18nProvider } from './I18nProvider'
import { LANGS, useI18n, type Notice } from './i18n'

// three.js is large; load it only once a model is shown.
const Preview = lazy(() => import('./components/Preview').then((m) => ({ default: m.Preview })))

const selectedFromHash = () => window.location.hash.replace(/^#\/?/, '') || null

export default function App() {
  return (
    <I18nProvider>
      <Shell />
    </I18nProvider>
  )
}

function Shell() {
  const { t, tm, lang, setLang } = useI18n()
  const [meta, setMeta] = useState<Meta | null>(null)
  const [designs, setDesigns] = useState<Design[]>([])
  const [selected, setSelected] = useState<string | null>(selectedFromHash)
  const [loaded, setDesign] = useState<Design | null>(null)
  const design = loaded && loaded.id === selected ? loaded : null
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<Notice | string | null>(null)
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
      if (ticket === latest.current) setError(e instanceof ApiError && e.notice ? e.notice : (e as Error).message)
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

  const [newProduct, setNewProduct] = useState<Product>('cutter')

  const upload = (file: File) =>
    track(async () => {
      const { design: created, job } = await api.upload(file, newProduct)
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
  const [privacyOpen, setPrivacyOpen] = useState(false)
  const hosting = meta?.hosting ?? null
  // A result from before switching Product does not match the files any more.
  const result = design?.result?.product === design?.product ? design?.result : null
  const coaster = design?.product === 'coaster'
  const colours = design && coaster
    ? ({ '--plate': design.coaster.plate_colour, '--motif': design.coaster.motif_colour } as CSSProperties)
    : undefined

  return (
    <div className="app">
      <header className="header">
        <img src="/logo.svg" alt="" />
        <h1>
          Pic<span>2</span>Cookie
        </h1>
        {meta && <span className="version">v{meta.version}</span>}
        <nav className="header-links">
          {hosting && (
            <>
              <a className="btn ghost" href={hosting.repository_url} target="_blank" rel="noreferrer">
                <CodeBracketIcon className="icon" /> {t('header.github')}
              </a>
              <button type="button" className="btn ghost" onClick={() => setPrivacyOpen(true)}>
                {t('header.privacy')}
              </button>
            </>
          )}
          <span className="segmented lang" role="group" aria-label={t('lang.label')}>
            {LANGS.map(([code, label]) => (
              <button key={code} type="button" className={code === lang ? 'on' : ''} onClick={() => setLang(code)}>
                {label}
              </button>
            ))}
          </span>
        </nav>
      </header>
      {hosting && privacyOpen && <PrivacyDialog hosting={hosting} onClose={() => setPrivacyOpen(false)} />}

      <aside className="sidebar">
        <ProductChoice value={newProduct} onChange={setNewProduct} />
        <Upload onFile={upload} product={newProduct} />
        {hosting && <UploadNotice onPrivacy={() => setPrivacyOpen(true)} />}
        <p className="section-title">{t('designs.title')}</p>
        <DesignList designs={designs} selected={selected} onSelect={select} />
      </aside>

      <main className="main">
        {error && (
          <div className="card error">
            <ExclamationTriangleIcon className="icon" /> {tm(error)}
          </div>
        )}
        {!design && (
          <>
            <div className="hero-choice">
              <ProductChoice value={newProduct} onChange={setNewProduct} />
            </div>
            <Upload onFile={upload} product={newProduct} hero />
          </>
        )}
        {design && meta && (
          <>
            <div className="title-row">
              <input
                aria-label={t('design.name')}
                defaultValue={design.name}
                key={design.id}
                onBlur={(e) => e.target.value.trim() && e.target.value !== design.name && patch({ name: e.target.value.trim() })}
                onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
              />
              <ProductChoice value={design.product} onChange={(product) => patch({ product })} />
              <span className="status">
                {busy || design.status === 'new' ? (
                  <>
                    <ArrowPathIcon className="icon spin" /> {t('status.generating')}
                  </>
                ) : design.status === 'ready' ? (
                  <>
                    <CheckCircleIcon className="icon" style={{ color: 'var(--green)' }} /> {t('status.ready')}
                  </>
                ) : null}
              </span>
              <button className="btn ghost" title={t('action.duplicate')} onClick={duplicate}>
                <DocumentDuplicateIcon className="icon" />
              </button>
              <button className="btn ghost danger" title={t('action.delete')} onClick={remove}>
                <TrashIcon className="icon" />
                {confirmDelete && t('action.confirmDelete')}
              </button>
            </div>

            {design.status === 'failed' && (
              <div className="card error">
                <ExclamationTriangleIcon className="icon" /> {design.error ? tm(design.error) : t('error.generic')}
              </div>
            )}

            <div className="workspace">
              <div className="side" style={{ minWidth: 0 }}>
                <div className="views">
                  <div className="card" style={colours}>
                    <h2>
                      {t('picture.title')} <span className="hint">{t('picture.hint')}</span>
                    </h2>
                    <div className="stage">
                      {result ? (
                        <RoleView
                          product={design.product}
                          outline={result.outline}
                          features={result.features}
                          onChange={changeRole}
                        />
                      ) : (
                        <div className="overlay">{t('picture.tracing')}</div>
                      )}
                    </div>
                    <Legend product={design.product} />
                  </div>
                  <div className="card">
                    <h2>
                      {t(coaster ? 'view.coaster' : 'view.cutter')}
                      <span className="hint">
                        <span className="segmented">
                          <button className={!flipped ? 'on' : ''} onClick={() => setFlipped(false)}>
                            {t(coaster ? 'view.top' : 'view.print')}
                          </button>
                          <button className={flipped ? 'on' : ''} onClick={() => setFlipped(true)}>
                            {t(coaster ? 'view.underside' : 'view.cutting')}
                          </button>
                        </span>
                      </span>
                    </h2>
                    <div className="stage">
                      {result ? (
                        <Suspense fallback={<div className="overlay">{t('view.loading3d')}</div>}>
                          <Preview
                            parts={productFiles(design).preview.map((p) => ({
                              url: fileUrl(design, p.file),
                              colour: p.colour,
                            }))}
                            flipped={flipped}
                          />
                        </Suspense>
                      ) : (
                        <div className="overlay">{t('view.generating')}</div>
                      )}
                    </div>
                  </div>
                </div>
                {result && result.warnings.length > 0 && (
                  <ul className="warnings">
                    {result.warnings.map((w) => (
                      <li key={w.text}>
                        <ExclamationTriangleIcon className="icon" /> {tm(w)}
                      </li>
                    ))}
                  </ul>
                )}
                {coaster ? (
                  <CoasterSettings design={design} onPatch={patch} />
                ) : (
                  <CutterSettings design={design} onPatch={patch} />
                )}
                {design.source.kind === 'raster' && <TraceSettings design={design} onPatch={patch} />}
              </div>

              <div className="side">
                <div className="card">
                  <h2>{t('estimate.title')}</h2>
                  {result ? <Estimate result={result} /> : <p className="note">{t('estimate.generating')}</p>}
                  <p className="note">{t('estimate.note')}</p>
                </div>
                <div className="card">
                  <h2>{t('print.title')}</h2>
                  <PrintSettings design={design} meta={meta} onPatch={patch} />
                  {result?.pause_z != null && (
                    <p className="note">{t('print.pause', { z: result.pause_z })}</p>
                  )}
                  {result && result.parts.length > 1 && (
                    <p className="note">{t('print.ams')}</p>
                  )}
                </div>
                {result && (
                  <div className="card">
                    <h2>{t('download.title')}</h2>
                    <Downloads design={design} hosted={!!hosting} />
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

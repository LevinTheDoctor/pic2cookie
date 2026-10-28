import { ArrowUpTrayIcon } from '@heroicons/react/24/outline'
import { useRef, useState, type DragEvent } from 'react'
import type { Product } from '../api'
import { useI18n } from '../i18n'

const ACCEPT = '.svg,.png,.jpg,.jpeg,.webp,image/svg+xml,image/png,image/jpeg,image/webp'

export function ProductChoice({ value, onChange }: { value: Product; onChange: (p: Product) => void }) {
  const { t } = useI18n()
  return (
    <span className="segmented product-choice" role="group" aria-label={t('product.label')}>
      {(['cutter', 'coaster'] as const).map((p) => (
        <button key={p} type="button" className={p === value ? 'on' : ''} onClick={() => onChange(p)}>
          {t(p === 'cutter' ? 'product.cutter' : 'product.coaster')}
        </button>
      ))}
    </span>
  )
}

export function Upload({
  onFile,
  product,
  hero = false,
}: {
  onFile: (file: File) => void
  product: Product
  hero?: boolean
}) {
  const { t } = useI18n()
  const input = useRef<HTMLInputElement>(null)
  const [active, setActive] = useState(false)

  const drop = (e: DragEvent) => {
    e.preventDefault()
    setActive(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <div
      className={`drop${hero ? ' hero' : ''}${active ? ' active' : ''}`}
      role="button"
      tabIndex={0}
      onClick={() => input.current?.click()}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setActive(true)
      }}
      onDragLeave={() => setActive(false)}
      onDrop={drop}
    >
      {hero && <img src="/logo.svg" alt="" />}
      {hero && <h2>{t('upload.hero')}</h2>}
      <ArrowUpTrayIcon className="icon" />
      <span>
        <strong>{t('upload.drop')}</strong> {t('upload.orClick')}{' '}
        {t(product === 'cutter' ? 'upload.makesCutter' : 'upload.makesCoaster')}
      </span>
      <span>{t('upload.types')}</span>
      <input
        ref={input}
        type="file"
        accept={ACCEPT}
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFile(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}

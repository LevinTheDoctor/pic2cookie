import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { fileUrl, type Design } from '../api'
import { useI18n } from '../i18n'

export function DesignList({
  designs,
  selected,
  onSelect,
}: {
  designs: Design[]
  selected: string | null
  onSelect: (id: string) => void
}) {
  const { t, num } = useI18n()
  if (!designs.length) return <p className="sub">{t('designs.empty')}</p>
  return (
    <ul className="designs">
      {designs.map((d) => (
        <li key={d.id}>
          <button className={d.id === selected ? 'selected' : ''} onClick={() => onSelect(d.id)}>
            {d.result ? (
              <img className="thumb" src={fileUrl(d, 'picture.svg')} alt="" loading="lazy" />
            ) : (
              <span className="thumb" />
            )}
            <span className="meta">
              <span className="name">{d.name}</span>
              <span className="sub">
                {d.status === 'failed' ? (
                  <>
                    <ExclamationTriangleIcon className="icon" style={{ width: 12, height: 12 }} /> {t('designs.failed')}
                  </>
                ) : d.result ? (
                  `${t(d.product === 'coaster' ? 'product.coaster' : 'product.cutter')} · ${num(d.result.estimate.grams)} g · ${Math.round(d.product === 'coaster' ? d.coaster.size : d.cutter.size)} mm`
                ) : (
                  t('designs.generating')
                )}
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}

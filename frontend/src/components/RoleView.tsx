import type { CSSProperties } from 'react'
import type { Feature, Product, Role } from '../api'
import { pathBounds } from '../geometry'
import { useI18n } from '../i18n'

const NEXT: Record<Product, Record<Feature['kind'], Partial<Record<Role, Role>>>> = {
  cutter: {
    region: { ignore: 'hole', hole: 'imprint', imprint: 'ignore' },
    line: { imprint: 'ignore', ignore: 'imprint' },
  },
  coaster: {
    region: { motif: 'ignore', ignore: 'motif' },
    line: {},
  },
}

export function RoleView({
  product,
  outline,
  features,
  onChange,
}: {
  product: Product
  outline: string
  features: Feature[]
  onChange: (feature: Feature, role: Role) => void
}) {
  const { t } = useI18n()
  const [minX, minY, maxX, maxY] = pathBounds(outline)
  const pad = Math.max(maxX - minX, maxY - minY) * 0.05
  const viewBox = `${minX - pad} ${minY - pad} ${maxX - minX + 2 * pad} ${maxY - minY + 2 * pad}`
  const ordered = [...features].sort(
    (a, b) => Number(a.kind === 'line') - Number(b.kind === 'line') || b.area - a.area,
  )
  return (
    <svg className={`roleview ${product}`} viewBox={viewBox} role="img" aria-label={t('picture.aria')}>
      <path className="outline" d={outline} fillRule="evenodd" />
      {ordered.map((f) => (
        <path
          key={f.id}
          className={`feature ${f.kind} ${f.role}`}
          d={f.path}
          fillRule="evenodd"
          onClick={() => {
            const next = NEXT[product][f.kind][f.role]
            if (next) onChange(f, next)
          }}
        >
          <title>{t('picture.featureTitle', { id: f.id, role: t(`role.${f.role}`) })}</title>
        </path>
      ))}
    </svg>
  )
}

export function Legend({ product }: { product: Product }) {
  const { t } = useI18n()
  const items: [string, CSSProperties][] =
    product === 'coaster'
      ? [
          [t('legend.plate'), { background: 'var(--plate)' }],
          [t('role.motif'), { background: 'var(--motif)' }],
          [t('role.ignore'), { borderStyle: 'dashed' }],
        ]
      : [
          [t('legend.cookie'), { background: 'var(--dough)' }],
          [t('role.hole'), { background: 'var(--hole)' }],
          [t('role.imprint'), { background: 'var(--imprint)' }],
          [t('role.ignore'), { borderStyle: 'dashed' }],
        ]
  return (
    <div className="legend">
      {items.map(([label, style]) => (
        <span key={label}>
          <i className="swatch" style={style} /> {label}
        </span>
      ))}
    </div>
  )
}

import type { Feature, Role } from '../api'
import { pathBounds } from '../geometry'

const NEXT: Record<Feature['kind'], Partial<Record<Role, Role>>> = {
  region: { ignore: 'hole', hole: 'imprint', imprint: 'ignore' },
  line: { imprint: 'ignore', ignore: 'imprint' },
}

export function RoleView({
  outline,
  features,
  onChange,
}: {
  outline: string
  features: Feature[]
  onChange: (feature: Feature, role: Role) => void
}) {
  const [minX, minY, maxX, maxY] = pathBounds(outline)
  const pad = Math.max(maxX - minX, maxY - minY) * 0.05
  const viewBox = `${minX - pad} ${minY - pad} ${maxX - minX + 2 * pad} ${maxY - minY + 2 * pad}`
  const ordered = [...features].sort(
    (a, b) => Number(a.kind === 'line') - Number(b.kind === 'line') || b.area - a.area,
  )
  return (
    <svg className="roleview" viewBox={viewBox} role="img" aria-label="Picture with roles">
      <path className="outline" d={outline} fillRule="evenodd" />
      {ordered.map((f) => (
        <path
          key={f.id}
          className={`feature ${f.kind} ${f.role}`}
          d={f.path}
          fillRule="evenodd"
          onClick={() => {
            const next = NEXT[f.kind][f.role]
            if (next) onChange(f, next)
          }}
        >
          <title>{`${f.id}: ${f.role} (click to change)`}</title>
        </path>
      ))}
    </svg>
  )
}

export function Legend() {
  return (
    <div className="legend">
      <span>
        <i className="swatch" style={{ background: 'var(--dough)' }} /> Cookie
      </span>
      <span>
        <i className="swatch" style={{ background: 'var(--hole)' }} /> Hole (Inner blade)
      </span>
      <span>
        <i className="swatch" style={{ background: 'var(--imprint)' }} /> Imprint blade
      </span>
      <span>
        <i className="swatch" style={{ borderStyle: 'dashed' }} /> Ignored
      </span>
    </div>
  )
}

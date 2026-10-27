import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { fileUrl, type Design } from '../api'

export function DesignList({
  designs,
  selected,
  onSelect,
}: {
  designs: Design[]
  selected: string | null
  onSelect: (id: string) => void
}) {
  if (!designs.length) return <p className="sub">No saved designs yet.</p>
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
                    <ExclamationTriangleIcon className="icon" style={{ width: 12, height: 12 }} /> failed
                  </>
                ) : d.result ? (
                  `${d.result.estimate.grams} g · ${Math.round(d.cutter.size)} mm`
                ) : (
                  'generating…'
                )}
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}

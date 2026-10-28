import type { DesignResult } from '../api'
import { useI18n } from '../i18n'

export function Estimate({ result }: { result: DesignResult }) {
  const { t, num } = useI18n()
  const { estimate: e, dimensions: d } = result
  return (
    <div className="estimate">
      <div className="stat">
        <div className="label">{t('estimate.filament')}</div>
        <div className="number">
          {num(e.grams)}
          <small>g</small>
        </div>
      </div>
      <div className="stat">
        <div className="label">{t('estimate.length')}</div>
        <div className="number">
          {num(e.metres)}
          <small>m</small>
        </div>
      </div>
      <div className="stat">
        <div className="label">{t('estimate.cost')}</div>
        <div className="number">{e.cost != null ? num(e.cost) : '–'}</div>
      </div>
      {result.parts.length > 1 && (
        <div className="stat parts">
          <div className="label">{t('estimate.perColour')}</div>
          {result.parts.map((part) => (
            <div key={part.name} className="part">
              <i className="swatch" style={{ background: part.colour ?? undefined }} />
              <span>{part.name === 'motif' ? t('part.motif') : part.name === 'plate' ? t('part.plate') : part.name}</span>
              <span className="grams">
                {num(part.estimate.grams)} g · {num(part.estimate.metres)} m
              </span>
            </div>
          ))}
        </div>
      )}
      <div className="stat">
        <div className="label">{t('estimate.size')}</div>
        <div className="number" style={{ fontSize: '1rem', paddingTop: 6 }}>
          {Math.round(d.width)} × {Math.round(d.depth)} × {num(d.height)}
          <small>mm</small>
        </div>
      </div>
    </div>
  )
}

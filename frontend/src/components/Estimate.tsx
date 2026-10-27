import type { DesignResult } from '../api'

export function Estimate({ result }: { result: DesignResult }) {
  const { estimate: e, dimensions: d } = result
  return (
    <div className="estimate">
      <div className="stat">
        <div className="label">Filament</div>
        <div className="number">
          {e.grams}
          <small>g</small>
        </div>
      </div>
      <div className="stat">
        <div className="label">Length</div>
        <div className="number">
          {e.metres}
          <small>m</small>
        </div>
      </div>
      <div className="stat">
        <div className="label">Cost</div>
        <div className="number">{e.cost != null ? e.cost.toFixed(2) : '–'}</div>
      </div>
      <div className="stat">
        <div className="label">Size</div>
        <div className="number" style={{ fontSize: '1rem', paddingTop: 6 }}>
          {Math.round(d.width)} × {Math.round(d.depth)} × {d.height}
          <small>mm</small>
        </div>
      </div>
    </div>
  )
}

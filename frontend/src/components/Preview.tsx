import { Bounds, Grid, OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { useEffect, useState } from 'react'
import { Box3, type BufferGeometry, Vector3 } from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { useI18n } from '../i18n'

const GREEN = '#00ae42'

export interface PreviewPart {
  url: string
  colour: string | null
}

interface Loaded {
  key: string
  geometries: BufferGeometry[]
  centre: Vector3
  height: number
}

/**
 * The Product as printed, standing on the plate. Parts share one coordinate
 * system, so they are centred together. A Cutter's STL is mirrored for
 * printing: "flipped" turns it blade down to show the picture the right way
 * round; for a Coaster it shows the underside.
 */
export function Preview({ parts, flipped }: { parts: PreviewPart[]; flipped: boolean }) {
  const { t } = useI18n()
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [error, setError] = useState<string | null>(null)
  const key = parts.map((p) => p.url).join('|')

  useEffect(() => {
    const abort = new AbortController()
    Promise.all(
      key.split('|').map((url) =>
        fetch(url, { signal: abort.signal }).then((r) => {
          if (!r.ok) throw new Error(String(r.status))
          return r.arrayBuffer()
        }),
      ),
    )
      .then((buffers) => {
        const geometries = buffers.map((buf) => new STLLoader().parse(buf))
        const box = new Box3()
        for (const geo of geometries) {
          geo.computeBoundingBox()
          box.union(geo.boundingBox!)
        }
        setLoaded((old) => {
          old?.geometries.forEach((g) => g.dispose())
          return { key, geometries, centre: box.getCenter(new Vector3()), height: box.max.z - box.min.z }
        })
        setError(null)
      })
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
    return () => abort.abort()
  }, [key])

  const floor = loaded ? -loaded.height / 2 - 0.01 : 0

  return (
    <>
      <Canvas camera={{ position: [0, 110, 140], fov: 40, near: 1, far: 5000 }} dpr={[1, 2]}>
        <ambientLight intensity={0.55} />
        <directionalLight position={[80, 160, 100]} intensity={1.6} />
        <directionalLight position={[-120, 60, -80]} intensity={0.5} />
        {loaded && (
          // Re-fit whenever new files are shown; the size may have changed.
          <Bounds key={loaded.key} fit clip observe margin={1.25}>
            {/* STL is z-up; three.js is y-up. */}
            <group rotation={[flipped ? Math.PI / 2 : -Math.PI / 2, 0, 0]}>
              <group position={loaded.centre.clone().negate()}>
                {loaded.geometries.map((geometry, i) => (
                  <mesh key={i} geometry={geometry}>
                    <meshStandardMaterial color={parts[i]?.colour ?? GREEN} roughness={0.55} metalness={0.05} />
                  </mesh>
                ))}
              </group>
            </group>
          </Bounds>
        )}
        <Grid
          position={[0, floor, 0]}
          args={[400, 400]}
          cellSize={10}
          sectionSize={50}
          cellColor="#9aa49e"
          sectionColor={GREEN}
          fadeDistance={500}
          infiniteGrid
        />
        <OrbitControls makeDefault enableDamping />
      </Canvas>
      {!loaded && !error && <div className="overlay">{t('view.loadingModel')}</div>}
      {error && <div className="overlay">{t('view.loadError', { status: error })}</div>}
    </>
  )
}

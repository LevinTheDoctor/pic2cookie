import { Bounds, Grid, OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { useEffect, useState } from 'react'
import type { BufferGeometry } from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'

const GREEN = '#00ae42'

/**
 * The Cutter as printed: flange on the plate. The STL is in print orientation
 * (mirrored picture); "cutting view" flips it over, blade down, which shows the
 * picture the right way round from above.
 */
export function CutterPreview({ url, flipped }: { url: string; flipped: boolean }) {
  const [geometry, setGeometry] = useState<BufferGeometry | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const abort = new AbortController()
    fetch(url, { signal: abort.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`Could not load the cutter (${r.status})`)
        return r.arrayBuffer()
      })
      .then((buf) => {
        const geo = new STLLoader().parse(buf)
        geo.computeBoundingBox()
        geo.center()
        setGeometry((old) => {
          old?.dispose()
          return geo
        })
        setError(null)
      })
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
    return () => abort.abort()
  }, [url])

  const box = geometry?.boundingBox
  const floor = box ? -(box.max.z - box.min.z) / 2 - 0.01 : 0

  return (
    <>
      <Canvas camera={{ position: [0, 110, 140], fov: 40, near: 1, far: 5000 }} dpr={[1, 2]}>
        <ambientLight intensity={0.55} />
        <directionalLight position={[80, 160, 100]} intensity={1.6} />
        <directionalLight position={[-120, 60, -80]} intensity={0.5} />
        {geometry && (
          <Bounds fit clip observe margin={1.25}>
            {/* STL is z-up; three.js is y-up. */}
            <group rotation={[flipped ? Math.PI / 2 : -Math.PI / 2, 0, 0]}>
              <mesh geometry={geometry}>
                <meshStandardMaterial color={GREEN} roughness={0.55} metalness={0.05} />
              </mesh>
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
      {!geometry && !error && <div className="overlay">Loading cutter…</div>}
      {error && <div className="overlay">{error}</div>}
    </>
  )
}

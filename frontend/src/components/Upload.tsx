import { ArrowUpTrayIcon } from '@heroicons/react/24/outline'
import { useRef, useState, type DragEvent } from 'react'

const ACCEPT = '.svg,.png,.jpg,.jpeg,.webp,image/svg+xml,image/png,image/jpeg,image/webp'

export function Upload({ onFile, hero = false }: { onFile: (file: File) => void; hero?: boolean }) {
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
      {hero && <h2>Turn a picture into a cookie cutter</h2>}
      <ArrowUpTrayIcon className="icon" />
      <span>
        <strong>Drop a picture</strong> or click to choose
      </span>
      <span>SVG, PNG, JPG or WebP</span>
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

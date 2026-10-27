import { ArrowDownTrayIcon, ArrowTopRightOnSquareIcon, CubeIcon } from '@heroicons/react/24/outline'
import { bambuStudioLink, fileUrl, type Design } from '../api'

export function Downloads({ design }: { design: Design }) {
  return (
    <div className="downloads">
      <a className="btn primary" href={bambuStudioLink(design)}>
        <ArrowTopRightOnSquareIcon className="icon" /> Open in Bambu Studio
      </a>
      <a className="btn" href={fileUrl(design, 'cutter.bambu.3mf', true)}>
        <CubeIcon className="icon" /> Bambu project (.3mf)
      </a>
      <div className="row">
        <a className="btn" href={fileUrl(design, 'cutter.stl', true)}>
          <ArrowDownTrayIcon className="icon" /> STL
        </a>
        <a className="btn" href={fileUrl(design, 'cutter.3mf', true)}>
          <ArrowDownTrayIcon className="icon" /> 3MF
        </a>
      </div>
      <div className="row">
        <a className="btn" href={fileUrl(design, 'picture.svg', true)}>
          <ArrowDownTrayIcon className="icon" /> Picture SVG
        </a>
        <a className="btn" href={fileUrl(design, 'roles.svg', true)} title="For pic2cookie make">
          <ArrowDownTrayIcon className="icon" /> Roles SVG
        </a>
      </div>
    </div>
  )
}

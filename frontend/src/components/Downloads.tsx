import { ArrowDownTrayIcon, ArrowTopRightOnSquareIcon, CubeIcon } from '@heroicons/react/24/outline'
import { bambuStudioLink, fileUrl, productFiles, type Design } from '../api'
import { useI18n } from '../i18n'

export function Downloads({ design, hosted = false }: { design: Design; hosted?: boolean }) {
  const { t } = useI18n()
  const files = productFiles(design)
  const coaster = design.product === 'coaster'
  return (
    <div className="downloads">
      {!hosted && (
        <a className="btn primary" href={bambuStudioLink(design)}>
          <ArrowTopRightOnSquareIcon className="icon" /> {t('download.openBambu')}
        </a>
      )}
      <a className={hosted ? 'btn primary' : 'btn'} href={fileUrl(design, files.bambu, true)}>
        <CubeIcon className="icon" /> {t('download.bambu')}
      </a>
      <div className="row">
        <a className="btn" href={fileUrl(design, files.stl, true)} title={coaster ? t('download.stlZipTitle') : undefined}>
          <ArrowDownTrayIcon className="icon" /> {t(coaster ? 'download.stlZip' : 'download.stl')}
        </a>
        <a className="btn" href={fileUrl(design, files.threemf, true)}>
          <ArrowDownTrayIcon className="icon" /> {t('download.threemf')}
        </a>
      </div>
      <div className="row">
        <a className="btn" href={fileUrl(design, 'picture.svg', true)}>
          <ArrowDownTrayIcon className="icon" /> {t('download.picture')}
        </a>
        {!coaster && (
          <a className="btn" href={fileUrl(design, 'roles.svg', true)} title={t('download.rolesTitle')}>
            <ArrowDownTrayIcon className="icon" /> {t('download.roles')}
          </a>
        )}
      </div>
    </div>
  )
}

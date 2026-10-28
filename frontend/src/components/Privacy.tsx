import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useEffect, useRef } from 'react'
import type { Hosting } from '../api'
import { useI18n } from '../i18n'

/** One line under the upload box: what happens to an uploaded picture. */
export function UploadNotice({ onPrivacy }: { onPrivacy: () => void }) {
  const { t } = useI18n()
  return (
    <p className="note upload-notice">
      {t('upload.notice')}{' '}
      <button type="button" className="link" onClick={onPrivacy}>
        {t('header.privacy')}
      </button>
    </p>
  )
}

/** The privacy notice (GDPR / DSGVO, Art. 13) of a hosted instance. */
export function PrivacyDialog({ hosting, onClose }: { hosting: Hosting; onClose: () => void }) {
  const { t } = useI18n()
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = dialog.current
    if (d && !d.open) d.showModal?.()
  }, [])
  const { name, address, email } = hosting.operator
  return (
    <dialog ref={dialog} className="privacy" onClose={onClose} aria-labelledby="privacy-title">
      <div className="privacy-head">
        <h2 id="privacy-title">{t('privacy.title')}</h2>
        <button type="button" className="btn ghost" title={t('action.close')} onClick={() => dialog.current?.close()}>
          <XMarkIcon className="icon" />
        </button>
      </div>

      <h3>{t('privacy.who')}</h3>
      {name || email ? (
        <p>
          {name}
          {address && (
            <>
              <br />
              {address}
            </>
          )}
          {email && (
            <>
              <br />
              <a href={`mailto:${email}`}>{email}</a>
            </>
          )}
        </p>
      ) : (
        <p className="warning-text">
          <ExclamationTriangleIcon className="icon" />
          <span>{t('privacy.noOperator')}</span>
        </p>
      )}

      <h3>{t('privacy.what')}</h3>
      <p>{t('privacy.whatText')}</p>
      <p>
        {hosting.retention_days
          ? t('privacy.keptDays', { days: hosting.retention_days })
          : t('privacy.keptUntilDeleted')}
      </p>

      <h3>{t('privacy.logs')}</h3>
      <p>{t('privacy.logsText')}</p>

      <h3>{t('privacy.cookies')}</h3>
      <p>{t('privacy.cookiesText')}</p>

      <h3>{t('privacy.rights')}</h3>
      <p>{t('privacy.rightsText')}</p>

      {hosting.privacy_url && (
        <p>
          <a href={hosting.privacy_url} target="_blank" rel="noreferrer">
            {t('privacy.full')}
          </a>
        </p>
      )}
      <p className="note">
        {t('privacy.openSource')}{' '}
        <a href={hosting.repository_url} target="_blank" rel="noreferrer">
          {hosting.repository_url.replace(/^https?:\/\//, '')}
        </a>
      </p>
    </dialog>
  )
}

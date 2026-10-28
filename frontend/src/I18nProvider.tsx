import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { I18nContext, initialLang, STORAGE_KEY, translator, type Lang } from './i18n'

/** Holds the chosen language, remembered in this browser only. */
export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang)

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const setLang = useCallback((next: Lang) => {
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // not remembered, but still switched
    }
  }, [])

  const value = useMemo(() => translator(lang, setLang), [lang, setLang])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

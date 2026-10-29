import { act, cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Design } from './api'
import App from './App'
import { Downloads } from './components/Downloads'
import { pathBounds } from './geometry'
import { I18nProvider } from './I18nProvider'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  localStorage.clear()
})

function stubApi(meta: object = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      const body = url.endsWith('/meta')
        ? { version: '0.1.0', printers: [], default_printer: 'a1mini', materials: {}, formats: [], defaults: {}, limits: {}, hosting: null, ...meta }
        : []
      return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } })
    }),
  )
}

describe('App', () => {
  it('shows the upload hero when no design is selected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        const body = url.endsWith('/meta')
          ? { version: '0.1.0', printers: [], default_printer: 'a1mini', materials: {}, formats: [], defaults: {}, limits: {} }
          : []
        return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } })
      }),
    )
    render(<App />)
    expect(screen.getByText('Turn a picture into a cookie cutter or coaster')).toBeInTheDocument()
    expect(await screen.findByText('v0.1.0')).toBeInTheDocument()
    expect(await screen.findByText('No saved designs yet.')).toBeInTheDocument()
    expect(screen.queryByText('GitHub')).not.toBeInTheDocument()
    expect(screen.queryByText('Privacy')).not.toBeInTheDocument()
  })

  it('links the source and the privacy notice when hosted', async () => {
    const hosting = {
      enabled: true,
      repository_url: 'https://github.com/LevinTheDoctor/pic2cookie',
      operator: { name: null, address: null, email: null },
      privacy_url: null,
      retention_days: 30,
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        const body = url.endsWith('/meta')
          ? { version: '0.1.0', printers: [], default_printer: 'a1mini', materials: {}, formats: [], defaults: {}, limits: {}, hosting }
          : []
        return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } })
      }),
    )
    render(<App />)
    const link = await screen.findByRole('link', { name: /GitHub/ })
    expect(link).toHaveAttribute('href', 'https://github.com/LevinTheDoctor/pic2cookie')
    screen.getAllByRole('button', { name: 'Privacy' })[0].click()
    expect(await screen.findByText('Privacy notice (GDPR)')).toBeInTheDocument()
    expect(screen.getByText(/for 30 days after their last change/)).toBeInTheDocument()
  })
})

describe('Downloads', () => {
  const design = { id: 'abc', product: 'cutter', result: null } as unknown as Design

  it('offers Open in Bambu Studio when run locally', () => {
    render(<I18nProvider><Downloads design={design} /></I18nProvider>)
    expect(screen.getByRole('link', { name: /Open in Bambu Studio/ })).toBeInTheDocument()
  })

  it('leaves out Open in Bambu Studio when hosted', () => {
    render(<I18nProvider><Downloads design={design} hosted /></I18nProvider>)
    expect(screen.queryByRole('link', { name: /Open in Bambu Studio/ })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Bambu project/ })).toHaveClass('primary')
  })
})

describe('pathBounds', () => {
  it('reads absolute M/L paths', () => {
    expect(pathBounds('M1 2L10 -3L4.5 20Z')).toEqual([1, -3, 10, 20])
  })
})

describe('languages', () => {
  it('switches to German and remembers it', async () => {
    stubApi()
    const { unmount } = render(<App />)
    expect(await screen.findByText('Turn a picture into a cookie cutter or coaster')).toBeInTheDocument()
    act(() => screen.getByRole('button', { name: 'DE' }).click())
    expect(screen.getByText('Aus einem Bild wird ein Ausstecher oder Untersetzer')).toBeInTheDocument()
    expect(await screen.findByText('Noch keine gespeicherten Entwürfe.')).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('de')
    unmount()
    render(<App />)
    expect(screen.getByText('Aus einem Bild wird ein Ausstecher oder Untersetzer')).toBeInTheDocument()
  })

  it('shows the German privacy notice', async () => {
    localStorage.setItem('pic2cookie.lang', 'de')
    stubApi({
      hosting: {
        enabled: true,
        repository_url: 'https://github.com/LevinTheDoctor/pic2cookie',
        operator: { name: 'Jane Doe', address: null, email: 'jane@example.org' },
        privacy_url: null,
        retention_days: 14,
      },
    })
    render(<App />)
    const [privacy] = await screen.findAllByRole('button', { name: 'Datenschutz' })
    act(() => privacy.click())
    expect(await screen.findByText('Datenschutzhinweis (DSGVO)')).toBeInTheDocument()
    expect(screen.getByText(/14 Tage nach ihrer letzten Änderung/)).toBeInTheDocument()
    expect(screen.getByText('jane@example.org')).toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { pathBounds } from './geometry'

afterEach(() => vi.unstubAllGlobals())

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
    expect(screen.getByText('Turn a picture into a cookie cutter')).toBeInTheDocument()
    expect(await screen.findByText('v0.1.0')).toBeInTheDocument()
    expect(await screen.findByText('No saved designs yet.')).toBeInTheDocument()
  })
})

describe('pathBounds', () => {
  it('reads absolute M/L paths', () => {
    expect(pathBounds('M1 2L10 -3L4.5 20Z')).toEqual([1, -3, 10, 20])
  })
})

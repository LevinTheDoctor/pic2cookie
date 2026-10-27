import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 1200 }, // three.js lives in its own lazy chunk
  server: {
    // The API runs separately in development (scripts/start.sh --dev).
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})

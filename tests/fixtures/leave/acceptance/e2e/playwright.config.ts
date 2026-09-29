import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['list'], ['json', { outputFile: 'results.json' }]],
  use: { baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:4173' },
})

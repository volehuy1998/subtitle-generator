/**
 * MSW browser worker — used in Vite dev mode when VITE_MOCK=true.
 *
 * One-time setup (run once per repo clone):
 *   cd frontend && npx msw init public/ --save
 *
 * Then start the dev server with:
 *   VITE_MOCK=true npm run dev
 */
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export const worker = setupWorker(...handlers)

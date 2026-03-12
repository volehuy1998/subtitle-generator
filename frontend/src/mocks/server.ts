/**
 * MSW Node server — used in Vitest tests via src/test/setup.ts.
 * Do not import this in browser code.
 */
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)

# SubForge Frontend

React SPA for the SubForge subtitle generator.

## Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Framework        | React 19 (StrictMode)               |
| Language         | TypeScript (strict)                 |
| Build            | Vite 6                              |
| State            | Zustand (taskStore, uiStore)        |
| Styling          | Tailwind CSS v4 + CSS custom properties |
| Real-time        | SSE (EventSource) + WebSocket       |
| Testing          | Vitest + Testing Library + MSW      |
| E2E              | Playwright (129 tests)              |

## Setup

```bash
npm install
npm run dev       # Dev server at http://localhost:5173 (proxies API to :8000)
npm run build     # Production build
npm run test      # Run all tests
npm run coverage  # Coverage report
```

## Architecture

```
src/
  pages/          App, StatusPage, AboutPage, ContactPage, SecurityPage
  components/     Organized by feature (transcribe/, embed/, progress/, output/, system/, layout/)
  hooks/          useSSE, useHealthStream, useTaskQueue
  store/          taskStore.ts (task state), uiStore.ts (UI chrome)
  api/            client.ts (typed HTTP client), types.ts (API types)
```

### State Management

- **taskStore**: Active task state (progress, segments, timings, download URLs). Single-task model.
- **uiStore**: UI state (active tab, health panel, SSE connection status, theme).

### Real-Time

Two independent SSE connections:
1. **Health stream** (`/health/stream`) -- mounted once at app root, feeds system status
2. **Task stream** (`/events/{taskId}`) -- per-task, handles 13 event types with exponential backoff

### Routing

Custom SPA router using `history.pushState` + custom `spa-navigate` events.

## Testing

372 unit/integration tests + 129 Playwright E2E tests covering:
- Store logic, hooks, API client
- Component rendering and interaction
- Responsive layouts, cross-browser behavior
- WCAG 2.1 AA accessibility
- Upload flow, embed flow, SPA navigation

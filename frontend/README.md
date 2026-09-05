# RecruitFlow Frontend

React + TypeScript + Vite + Tailwind CSS v4 frontend for RecruitFlow.

See the main project [README.md](../README.md) for full setup instructions, architecture notes, and business rules. Quick start:

```bash
npm install
cp .env.example .env   # set VITE_API_URL to your backend URL
npm run dev
```

## Structure

```
src/
  api/          TanStack Query hooks per backend resource (jobs, applications, panel, feedback, interviews, alerts, dashboard)
  components/   Reusable UI: Layout (sidebar nav), PipelineStepper, StageBadge, Toast, modals
  hooks/        useAuth (login/logout/current user)
  lib/          api client (axios + cookie auth), shared TypeScript types mirroring backend schemas
  pages/        One component per route
```

## Design system

- Fonts: `Newsreader` (serif, headings/numerals) + `Public Sans` (UI/data), loaded via Google Fonts in `index.css`.
- Colors: defined as CSS variables in the `@theme` block of `src/index.css` (pine green for progress/primary actions, amber for stall alerts, cool paper/ink neutrals).
- The pipeline stage is always shown as a literal stepper (`PipelineStepper`) on the application detail page, and as a compact `StageBadge` in tables - this is a deliberate design principle, not just two components that happened to exist.

## State management

Server state (everything from the API) lives entirely in TanStack Query - there's no separate Redux/Zustand store. Mutations invalidate the relevant query keys on success so the UI reflects the backend's actual state rather than an optimistic guess. Auth state is just the `['auth', 'me']` query - logging in/out sets or clears that cache entry directly.

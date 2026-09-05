# RecruitFlow — Design Documentation

## Design intent

RecruitFlow is an internal productivity tool for recruiters, not a marketing site or consumer app. The goal was to make it feel like a well-run paper trail — structured, calm, and confident — rather than another gradient-and-shadow SaaS dashboard template. Every design decision below was chosen deliberately to avoid the generic "AI-generated SaaS" look (warm cream + terracotta palettes, card-shadow-everywhere layouts, ALL-CAPS eyebrow labels).

---

## Typography

Two families, each with one clear job:

| Family | Role | Where |
|---|---|---|
| **Newsreader** (serif) | Headings, page titles, big dashboard numerals | `font-serif` |
| **Public Sans** (grotesk sans) | Everything else: body text, UI labels, table data | `font-sans` (default) |

**Why a serif for headings**: Newsreader reads like a credential or a paper form — fitting for a recruitment tool where the product's whole job is tracking formal decisions about people. It's used sparingly (page titles, the app wordmark, dashboard metric numbers) so it stays a deliberate accent rather than the whole interface's voice.

Loaded via Google Fonts in `src/index.css`, both variable-weight for crisp rendering at any size used.

---

## Color

Defined as CSS custom properties in `src/index.css`'s `@theme` block (Tailwind CSS v4), so every color is a named token, not a hardcoded hex scattered through components.

| Token | Value | Usage |
|---|---|---|
| `--color-paper` | `#F7F8F6` | Page background — cool off-white, not warm cream |
| `--color-surface` | `#FFFFFF` | Cards, inputs, modals |
| `--color-ink` | `#161D1A` | Primary text — near-black with a faint green undertone, not pure `#000` |
| `--color-ink-soft` | `#4B534F` | Secondary text, labels |
| `--color-line` | `#DBDFDB` | Borders, dividers |
| `--color-line-soft` | `#EAEDEA` | Table stripe backgrounds, subtle fills |
| `--color-pine` | `#1F6F5C` | **The one accent color.** Primary actions, forward progress, success |
| `--color-pine-deep` | `#175445` | Hover state for pine |
| `--color-pine-soft` | `#E6EFEC` | Pine-tinted backgrounds (badges, highlighted stepper dot) |
| `--color-amber` | `#B5651D` | **Reserved exclusively for stall alerts.** Never used decoratively |
| `--color-rose` | `#A23B3B` | Destructive actions (reject), error states |

**Why one accent, not a rainbow**: color is meaningful, not decorative. Pine green always means "moving forward / go." Amber always means "this needs attention." Rose always means "destructive / stop." If everything were colorful, nothing would carry information.

---

## Layout principles

1. **Hairlines over shadows.** Structure comes from `border` and `divide-y`/`divide-x`, not `box-shadow`. Tables, the dashboard's metric row, and section separators all use 1px borders in `--color-line`. This is the biggest single departure from the generic "card with shadow" SaaS template look.
2. **Numbers earn attention through scale, not chrome.** Dashboard headline metrics (`Metric` component in `DashboardPage.tsx`) are large serif numerals with a small label underneath — no icon, no colored background, no gradient card. The number itself is the design.
3. **Left-aligned, dense, functional.** This is a tool recruiters use all day, not a page they admire once. Tables are information-dense with generous but not wasteful spacing (`py-2.5` row height, not `py-6` marketing-site spacing).
4. **The pipeline is the interface's spine.** Wherever a candidate's stage matters, it's shown as a literal stepper (see below) — not just a colored word.

---

## The pipeline stepper (`PipelineStepper.tsx`)

The single most important custom component in the app. Rather than showing a candidate's stage as one colored badge, the application detail page renders the *entire* pipeline as a horizontal sequence of dots and connecting lines, with the candidate's actual position highlighted:

```
● ─── ● ─── ◉ ─── ○ ─── ○
Applied  Screening  Interview  Offer  Hired
         (past)    (current)  (future)
```

- Past stages: filled pine dot, connecting line filled pine
- Current stage: filled pine dot with a soft ring halo (`ring-4 ring-pine-soft`) for emphasis
- Future stages: hollow grey dot, grey connecting line
- **Rejected state**: the stepper still shows how far the candidate got (e.g. `Applied → Screening → Interview →`) before appending a distinct rose-colored "Rejected" marker — so rejection never erases the record of progress made. This directly reflects the reinstatement business rule (reinstating returns to that exact point, not to Applied) in the visual design.

For dense contexts (table rows) where the full stepper would be too wide, `StageBadge.tsx` provides a compact single-word pill instead — using the same color logic (pine for active progress, pine-solid for Hired, rose for Rejected) so the two representations stay visually consistent.

---

## Component patterns

- **Modals** (`NewApplicationModal`, `JobFormModal`, `ScheduleInterviewModal`): simple centered overlay, `bg-ink/30` scrim, no animation library — deliberately minimal rather than adding motion for its own sake.
- **Toasts** (`Toast.tsx`): bottom-right stack, auto-dismiss after 4s, icon + message, manually dismissable. Success uses a pine check icon; errors use a rose X icon — consistent with the color system above.
- **Bulk results** (`BulkResultsPanel.tsx`): deliberately *not* a toast, because bulk-action results can be a long list with mixed success/failure that a person needs to actually read, not glance at and lose. Shown as a dismissible inline panel with a scrollable list, each row explicitly showing success (pine check) or failure (rose X + reason) — this directly implements the "never hide bulk-action failures" requirement.
- **Error boundary** (`ErrorBoundary.tsx`): wraps the entire app to catch React rendering errors and show a friendly fallback screen instead of a white crash page. Added after the blank white page issue was observed in production on bad navigation.
- **Empty states**: every list (jobs, applications, alerts, feedback, panel, interviews) has a written empty-state message rather than just showing nothing — e.g. Alerts' empty state reads "No stalled candidates right now. Nice work keeping things moving," turning an empty list into a small positive signal rather than a dead end.

---

## Accessibility

- Every interactive icon-only button has an `aria-label` (remove interviewer, dismiss toast, close modal, etc.)
- Focus is always visible: a global `:focus-visible` outline in pine green, applied via plain CSS so it can never be accidentally suppressed by a component-level `outline-none`
- Modals use `role="dialog"` / `role="alertdialog"` with `aria-modal="true"` and `aria-labelledby` pointing at their heading
- `prefers-reduced-motion` is respected globally (all animations/transitions collapse to near-zero duration)
- Semantic HTML throughout: real `<table>` for tabular data, real `<label htmlFor>` pairing on every form input, real `<button>` elements for actions (never a styled `<div>` with an onClick)

---

## What was deliberately left out

Per the "restraint over decoration" principle:
- No page transition animations
- No illustration/hero imagery anywhere (this is a tool, not a landing page)
- No dark mode (not requested, and would have doubled the design surface for a v1 internal tool)
- No custom icon set — Lucide React's existing icon library is used as-is (lucide-react v1.x), since a bespoke icon set would be effort spent on decoration rather than function

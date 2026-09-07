---
charter: kanban-ui
status: validated
risk_level: low
milestone: v1.2
revision: 1
charter-revision: 12
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
source-manifest:
  sha: "5477684"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_js/visual-refresh-beh-1-design-tokens.test.js
    - tests_js/visual-refresh-beh-2-priority-stripe.test.js
    - tests_js/visual-refresh-beh-3-issue-key.test.js
    - tests_js/visual-refresh-beh-4-column-count.test.js
    - tests_js/visual-refresh-beh-5-switcher-plate.test.js
    - tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js
    - tests_js/visual-refresh-beh-7-8-accessibility-css.test.js
    - tests_js/visual-refresh-no-cdn-fonts.test.js
  computed-at: "2026-09-07T11:25:44.916Z"
---

# Live Spec: Visual design refresh — dispatch-board identity

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

<!-- This spec is presentation-only: it restyles board-view and issue-crud-forms' existing
     DOM without changing any fetch/render/mutation behavior those two specs already define.
     Every behavior below is a visual/styling contract, verifiable by inspection (screenshot
     or DOM+computed-style read), not a new data flow. -->

### Preconditions

- The `board-view` and `issue-crud-forms` specs are implemented and validated — this spec
  restyles their existing markup and DOM hooks, it does not add or remove any element ids,
  classes, or data attributes those specs' (and `ui-e2e`'s) tests depend on.
- No build step is introduced — `static/` stays plain HTML/CSS/vanilla JS, same as every prior
  kanban-ui capability; no bundler, framework, or CSS preprocessor is added.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the board page loads, **then** the page/board background renders as a
  solid deep pine-teal-black (`--ink: #16261F`) and each column renders as a mid-tone pine rail
  panel (`--rail: #2F4A3E`) — replacing the prior generic light-grey SaaS palette — with no
  change to which Projects/Issues are fetched or how they are grouped (board-view BEH-1/BEH-2
  unaffected).
- **BEH-2** — **When** an issue card renders, **then** it shows a warm off-white ticket-stock
  surface (`--paper: #F1ECDD`), a single hard offset shadow (no soft blurred grey glow), sharp
  or near-sharp corners (2-3px or none), and a 4-6px solid left-edge stripe colored by priority
  (`--stamp-red: #A3402F` high, `--stamp-gold: #B98A2E` medium, `--stamp-green: #4C7A5E` low) —
  while the card's `.card` class, `data-issue-id` attribute, and `draggable="true"` remain
  exactly as `board-view`/`issue-crud-forms` left them.
- **BEH-3** — **When** an issue card renders, **then** it shows the issue's key in a monospace
  face (`ui-monospace, "SF Mono", "Cascadia Code", "Roboto Mono", monospace`), the summary in
  regular-weight sans, a sentence-case type+priority meta line (e.g. "task · medium", never
  tracked-out caps), and the assignee — all in sentence case, no ALL-CAPS labels.
- **BEH-4** — **When** a column header renders, **then** it shows the status name in sentence
  case ("To do", "In progress", "Done") plus a small mono badge showing that column's issue
  count, with a brass-toned (`--stamp-gold`) rule beneath the header row.
- **BEH-5** — **When** the project switcher renders, **then** it is styled as a bordered
  plate/tab control (mono/brass treatment, not the default browser `<select>` chrome) while
  remaining the same functional `<select id="project-switcher">` element with its existing
  `change` event contract.
- **BEH-6** — **When** any of the three forms (create-project, create-issue, edit-issue)
  renders, **then** it uses the `--paper`/`--ink-line` palette, sharp corners, and a primary
  action button styled from the palette (`--rail` or `--stamp-gold` background, never a generic
  blue) — with no change to any field's `id`, `name`, `required` attribute, or submit/cancel
  wiring.
- **BEH-7** — **When** any focusable control (button, input, select, or card) receives keyboard
  focus, **then** a visible `:focus-visible` outline is shown, distinguishable against both
  `--ink` and `--paper` surfaces — never `outline: none` without a replacement.
- **BEH-8** — **When** the viewer's browser/OS reports `prefers-reduced-motion: reduce`,
  **then** any transition or animation this refresh adds (e.g. a hover lift on cards/buttons)
  is disabled or reduced to near-zero duration.

### Postconditions

- Every element id, class name, and data attribute that `board-view.spec.md`,
  `issue-crud-forms.spec.md`, and `ui-e2e.spec.md` depend on (`#board`, `#board-error`,
  `#project-switcher`, `.column[data-status]`, `.cards`, `.card[data-issue-id]`,
  `#create-issue`, `#edit-issue`, `#create-issue-form`, `#edit-issue-form`, `#delete-issue`,
  etc.) is unchanged after this refresh — only CSS and, where strictly needed for the new
  visual content (issue key, count badge, priority stripe), additive markup/attributes.
- Body text against its surface (`--ink`-on-page chrome, `--ink`/dark text on `--paper` cards
  and forms) meets at least WCAG AA contrast (4.5:1 normal text, 3:1 large text/UI components).
- No network request for fonts or other remote assets is introduced — every typeface is a
  system font-stack fallback chain; the app remains fully offline-capable.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| An issue's `priority` value is missing or not one of `low`/`medium`/`high` (defensive — the API only ever emits these three) | Card falls back to a neutral stripe color rather than rendering no stripe or a broken/empty style | `UI_STYLE_UNKNOWN_PRIORITY` |
| Card summary, assignee, or issue key text is long enough to overflow the card's fixed width | Text wraps or truncates with ellipsis; the card never overflows into a neighboring column or off the rail | `UI_STYLE_TEXT_OVERFLOW` |
| `prefers-reduced-motion: reduce` is set | Every transition/animation added by this refresh is disabled or reduced to near-zero duration | `UI_STYLE_MOTION_REDUCED` |

## System Constitution Reference

- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint, no real
  credentials." — Applies directly to typography: the distinctive look comes from system font
  stacks (weight, spacing, scale) only — no Google Fonts `<link>`, no remote `@font-face`, no
  bundled font files fetched at runtime.
- **Existing kanban-ui convention (no build step):** kanban-ui ships as static assets with no
  bundler/framework/preprocessor (established by every prior kanban-ui spec). Applies because
  this refresh is CSS/vanilla-JS-only — it must not introduce a package.json toolchain, a CSS
  preprocessor, or a component framework.
- **Quality Attribute (kanban-ui charter):** "Performance — board of a few dozen issues renders
  with no perceptible lag on a local connection." — Applies because the added stripe/shadow/
  badge treatment is plain CSS plus a few characters of additional markup per card, with no
  added client-side computation or network round-trip.
- **Principle:** "No inbound dependencies." — Applies because this refresh adds no dependency
  on any other repo or external service; it only touches this module's own static assets.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Design tokens | Add CSS custom properties (`--ink`, `--rail`, `--paper`, `--stamp-red`, `--stamp-gold`, `--stamp-green`, `--ink-line`, derived neutrals) to `board.css` `:root` | small |
| Page/column shell restyle | Restyle `body`, `header`, `#board`, `.column`, `.column h2` to the ink/rail palette; add brass rule under column headers | medium |
| Column count badge | Add a small mono issue-count badge next to each column header's label, wired from `board.js`'s render path | small |
| Card restyle + key | Restyle `.card` (paper surface, sharp corners, hard offset shadow, left priority stripe); add the issue's mono key to `board-logic.js`'s `buildCardHtml` | medium |
| Project switcher restyle | Restyle `#project-switcher` as a bordered plate/tab control via CSS (`appearance: none` + custom chrome), same `<select>` element | small |
| Form restyle | Restyle create-project/create-issue/edit-issue forms and their buttons to the palette | medium |
| Focus/motion accessibility | Add deliberate `:focus-visible` styling and a `prefers-reduced-motion` guard around any added transitions | small |

## Visual Expectations

<!-- For UI tasks only. Describes what the user SEES, verified by inspection/screenshot. -->

- **Page background:** solid `--ink` (#16261F). No gradients anywhere in this refresh.
- **Header:** "mock-jira" title in heavy weight (700-800), tight letter-spacing, system
  sans-serif stack (`-apple-system, "Segoe UI", "Inter", system-ui, sans-serif`).
- **Columns:** `--rail` (#2F4A3E) panel background. Header row shows the column label in
  sentence case ("To do", "In progress", "Done") plus a small mono badge with the issue count
  (e.g. "2"), and a 2px brass-toned (`--stamp-gold`) rule beneath the header row.
- **Cards:** `--paper` (#F1ECDD) background, 2-3px corner radius (or none), one hard offset
  shadow (e.g. `2px 2px 0 rgba(0,0,0,.35)`, no blur), a 4-6px solid left-edge priority stripe
  (`--stamp-red`/`--stamp-gold`/`--stamp-green`). Content top-to-bottom: issue key in mono,
  summary in medium-weight sans, a sentence-case "type · priority" meta line, assignee.
- **Project switcher:** styled as a bordered plate — `--ink-line` border, mono/brass accent,
  custom (non-default-OS) chrome — while remaining a real, keyboard-operable `<select>`.
- **Forms:** `--paper` background, `--ink-line` 1px borders on inputs, sharp corners, primary
  submit button in `--rail` or `--stamp-gold` with `--paper` text; cancel/secondary buttons
  outlined; delete button uses a `--stamp-red`-toned treatment.
- **Focus state:** a visible 2px outline (offset 2px) in a color that reads against both
  `--ink` and `--paper` surfaces, on every button/input/select/card.
- **Motion:** any hover/transition added (e.g. a subtle card lift) is disabled under
  `prefers-reduced-motion: reduce`.
- **Mobile (< 768px):** out of scope — the parent charter already excludes mobile-responsive
  polish; no breakpoint work is required or expected here.

## Acceptance Criteria

- [ ] Page/board background renders `--ink`; columns render as `--rail` panels with a brass rule under each header (BEH-1, BEH-4)
- [ ] Issue cards render on `--paper` with a left priority stripe colored by priority, a hard offset shadow, and sharp/near-sharp corners (BEH-2)
- [ ] Cards show the issue key in mono, summary, sentence-case type+priority meta, and assignee (BEH-3)
- [ ] Column headers show sentence-case status names with a mono issue-count badge (BEH-4)
- [ ] Project switcher is styled as a plate/tab control while remaining the same `<select id="project-switcher">` (BEH-5)
- [ ] All three forms are restyled to the palette with sharp corners and `--ink-line` borders, with no field id/name/required-attribute changes (BEH-6)
- [ ] Keyboard focus remains visible via a deliberate `:focus-visible` style on every interactive element (BEH-7)
- [ ] `prefers-reduced-motion: reduce` disables/reduces every added transition (BEH-8)
- [ ] No existing `board-view`/`issue-crud-forms`/`ui-e2e` DOM hooks (ids, classes, data attributes) are broken — `tests_js/` and `tests_e2e/test_ui_*.py` pass unmodified, or with locator-only fixes, never a weakened assertion
- [ ] No CDN font or other external network request is introduced — system font stacks only
- [ ] Paper-on-ink and ink-on-paper text contrast meets WCAG AA
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced

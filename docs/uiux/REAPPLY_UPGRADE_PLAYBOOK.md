# UI/UX Upgrade Reapply Playbook (Branch Transfer)

Date: 2026-03-09
Purpose: Re-apply the full premium UI/UX upgrade on another branch/folder quickly and consistently.

## How to use this file
1. Copy this file into the target branch/folder.
2. Ask Codex: "Apply `docs/uiux/REAPPLY_UPGRADE_PLAYBOOK.md` exactly."
3. Codex should execute phases in order and run the listed verification checks.

## Source scope to reproduce
Recreate all completed phases from this branch:
- Phase 0: Baseline/safety docs
- Phase 1: Visual foundation layer
- Phase 2: Shared camera/form component classes
- Phase 3: UX behavior polish (active nav + mobile nav collapse)
- Phase 4: Accessibility hardening
- Phase 5: Safe performance hints (image loading)
- Phase 6: Inline-style consolidation on key templates
- Final release prep docs

## Files to add (new)
### CSS
- `static/css/ui-phase1-foundation.css`
- `static/css/ui-phase2-components.css`
- `static/css/ui-phase3-ux.css`
- `static/css/ui-phase4-accessibility.css`
- `static/css/ui-phase6-cleanup.css`

### Docs
- `docs/uiux/phase-0-uiux-baseline.md`
- `docs/uiux/phase-0-checklist.md`
- `docs/uiux/phase-2-notes.md`
- `docs/uiux/phase-3-notes.md`
- `docs/uiux/phase-4-notes.md`
- `docs/uiux/phase-5-notes.md`
- `docs/uiux/phase-5-release-checklist.md`
- `docs/uiux/phase-6-notes.md`
- `docs/uiux/final-release-prep.md`
- `docs/uiux/final-regression-matrix.md`

## Files to modify
- `templates/base.html`
- `templates/index.html`
- `templates/admin/admin_dashboard.html`
- `templates/admin/admin_signup.html`
- `templates/clients/add.html`
- `templates/clients/edit.html`

## Deterministic reapply checklist

### Step A: Base layout integration (`templates/base.html`)
- Set `<html lang="en">`.
- Add body class: `<body class="ui-phase1">`.
- Add landmark roles:
  - nav: `role="navigation" aria-label="Primary"`
  - main: `id="main-content" role="main"`
  - footer: `role="contentinfo"`
- Include all phase CSS files in `<head>` after `custom.css` in this order:
  1. `ui-phase1-foundation.css`
  2. `ui-phase2-components.css`
  3. `ui-phase3-ux.css`
  4. `ui-phase4-accessibility.css`
  5. `ui-phase6-cleanup.css`
- Keep all existing IDs used by JS.
- Add/keep Phase 3 script in final script block:
  - auto active nav class `.is-active` based on `window.location.pathname`
  - mobile nav auto-collapse on link click for widths `< 992`
- Replace inline style snippets with utility classes where already standardized:
  - icon margin-right styles -> `.icon-gap-5`
  - troubleshoot modal hidden/padding -> `.is-hidden-initial`, `.modal-action-pad`

### Step B: Home page performance (`templates/index.html`)
- Hero carousel image attributes:
  - Slide 1: `fetchpriority="high" decoding="async"`
  - Slides 2-4: `loading="lazy" decoding="async"`
- Replace clean card-link inline style with class `.clean-link`.

### Step C: Component standardization (camera/form templates)
Apply class-based replacements in:
- `templates/clients/add.html`
- `templates/clients/edit.html`
- `templates/admin/admin_signup.html`

Required class usage:
- Loading overlay -> `.loading-overlay`
- Spinner size -> `.loading-spinner`
- Form shell max width -> `.form-shell-card`
- Camera layers:
  - video -> `.camera-video-layer`
  - canvas -> `.camera-canvas-layer`
  - preview image -> `.camera-preview-layer`
- Placeholder elements:
  - container -> `.camera-placeholder`
  - icon -> `.camera-placeholder-icon`
  - text -> `.camera-placeholder-text`
- Buttons:
  - start -> `.camera-action-btn`
  - retake -> `.camera-retake-btn`
  - capture -> `.camera-capture-btn`
- Thumbnails:
  - container -> `.capture-thumb`
  - image -> `.capture-thumb-img`
  - label -> `.capture-thumb-label`
  - tick -> `.capture-thumb-tick`
- Hidden initial controls -> `.capture-controls-initial`
- Message overlay default hidden -> `.message-overlay-hidden`
- Message overlay accessibility attributes:
  - `aria-live="polite"`
  - `aria-atomic="true"`
- Admin signup email input class:
  - `.input-force-lowercase`

### Step D: Dashboard cleanup (`templates/admin/admin_dashboard.html`)
- Replace inline styles with classes:
  - backup file input -> `.upload-input-hidden`
  - chart panel wrapper -> `.chart-min-panel`
  - min-width wrapper -> `.minw-0`
  - admin profile image -> `.dashboard-profile-photo`
  - active clients container -> `.dashboard-active-clients`
  - dynamic text-left wrappers -> `.active-client-meta`
- Keep existing JS/chart behavior unchanged.

### Step E: Base image loading hints
- In `templates/base.html`:
  - navbar logo image: `fetchpriority="high" decoding="async"`
  - footer logo image: `loading="lazy" decoding="async"`
- In `templates/admin/admin_dashboard.html`:
  - admin profile image: `loading="lazy" decoding="async"`

## Acceptance criteria (must pass)
- No JS-bound IDs removed/renamed.
- No duplicate `class` attributes.
- No malformed literal tokens from scripted edits.
- Manual checks pass for blocking routes:
  - `/client-log`, `/add`, `/edit/<id>`, `/admin/login` + face login, `/admin/signup`
- Theme, nav behavior, and responsiveness remain functional.

## Fast verification commands
Run these after reapply:
1. Duplicate class attributes:
   - search for `class="..." class="..."`
2. Leftover inline styles in target templates:
   - inspect `templates/base.html`, `templates/index.html`, `templates/admin/admin_dashboard.html`, `templates/admin/admin_signup.html`, `templates/clients/add.html`, `templates/clients/edit.html`
3. Confirm CSS includes in `templates/base.html` for all phase files.

## Release sign-off docs to use
- `docs/uiux/phase-5-release-checklist.md`
- `docs/uiux/final-regression-matrix.md`
- `docs/uiux/final-release-prep.md`

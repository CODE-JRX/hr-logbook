# Phase 0 UI/UX Baseline (No-Damage Gate)

Date: 2026-03-09  
Workspace: `C:\Users\JRX\Desktop\hrmo-e-logbook-v2`

## 1) Objective
Create a frozen baseline before any premium UI/UX redesign so we avoid regressions in critical flows.

## 2) Current UI Risk Snapshot
- Global stylesheet size: `static/css/custom.css` is ~`2081` lines.
- Template-level `<style>` blocks: `18`.
- Inline `style=` attributes across templates: `171`.
- Camera flow markup/scripts are duplicated across multiple templates.
- Global shell (`templates/base.html`) includes shared nav, footer, and global modals with JS bindings.

## 3) Route Coverage For Baseline Checks
Use these as mandatory pre/post redesign checkpoints.

- `/` (Home)
- `/client-log`
- `/client-log-help`
- `/add`
- `/clients` (admin)
- `/edit/<id>` (admin)
- `/client-log-report`
- `/csm-report`
- `/CSM-form`
- `/admin/login` (password + face path)
- `/admin/dashboard`
- `/admin/signup`
- `/admin/profile`
- `/terms-of-use`
- `/privacy-policy`

## 4) Screenshot Matrix (Baseline + Regression)
Capture each route in:
- Desktop light mode
- Desktop dark mode
- Mobile light mode
- Mobile dark mode

Recommended device widths:
- Desktop: `1440x900`
- Mobile: `390x844`

Capture at least these states:
- Default idle page state
- One primary interaction state (opened modal, hovered menu, loaded table, or active form)

## 5) Frozen Selector Contract (Do Not Rename In Early Redesign)
These selectors are JS-bound and high-risk. Keep stable through Phase 1-2.

### Global Shell (`templates/base.html`)
- `#theme-toggle`, `#theme-icon`
- `#deleteModal`, `#clientName`, `#confirmDeleteBtn`
- `#dbErrorModal`, `#btn-troubleshoot`, `#btn-refresh`, `#fixing-section`, `#troubleshoot-result`
- `#navBrandWrapper`

### Client Log (`templates/client_log.html`)
- `#video`, `#canvas`, `#preview`, `#scan-line`, `#loading-border`
- `#camera-placeholder`, `#camera-action`, `.camera-card`
- `#matchModal`, `#purposeModal`, `#additionalInfoModal`, `#logoutConfirmModal`, `#overrideModal`
- `#manual_search`, `#search_suggestions`, `#systemLog`
- `#status-text`, `#status-dot`, `#camera-status`, `#camera-error`
- `#btn_thats_me`, `#btn_not_me`, `#btn_purpose_next`, `#btn_purpose_cancel`, `#btn_info_back`, `#btn_info_close`, `#btn_time_in`, `#btn_confirm_logout`

### Add Client (`templates/clients/add.html`)
- `#addClientForm`, `#loadingOverlay`
- `#cameraCanvas`, `#video`, `#canvas`, `#preview`, `#camera-placeholder`, `#camera-action`
- `#capture-controls`, `#capture-btn`, `#retake-btn`, `#capture-target`, `#instruction-text`
- `#preview-center`, `#preview-left`, `#preview-right`
- `#tick-center`, `#tick-left`, `#tick-right`
- `#photo_data_center`, `#photo_data_left`, `#photo_data_right`
- `#saveBtn`, `#cancelBtn`, `#message-overlay`

### Edit Client (`templates/clients/edit.html`)
- `#editClientForm`, `#loadingOverlay`
- Camera and capture IDs mirrored from Add Client flow

### Admin Signup (`templates/admin/admin_signup.html`)
- `#adminSignupForm`, `#loadingOverlay`
- Shared camera/capture IDs used by scripts
- `#signupBtn`, `#message-overlay`

### Admin Face Login (`templates/admin/face_login.html`)
- `#video`, `#canvas`, `#preview`, `#scan-line`, `#camera-placeholder`, `#camera-action`, `.camera-card`
- `#pinModal`, `#pinInput`, `#pinError`
- `#login-status`, `#error`

### Reports / Dashboard
- `#filterForm`, `#searchInput`, `#logsTable`, `#exportCsvBtn` (`client_log_report.html`)
- `#filter-form`, `#csm-report` table scope (`csm_report.html`)
- `#chartActivity`, `#chartPurpose`, `#adminActiveClients`, `#backupFile`, `#restoreForm` (`admin_dashboard.html`)

## 6) No-Damage Acceptance Criteria (Must Pass)
Before approving any UI redesign batch:

- Navigation works in both auth states (admin vs non-admin).
- Theme toggle works and persists.
- Global modals still open/close correctly.
- Client Log camera starts, identifies, and modal sequence works.
- Manual override search in Client Log works.
- Add/Edit client 3-angle capture flow works.
- Admin face login + PIN verification works.
- Report filtering and export still works.
- Dashboard charts render.
- No horizontal overflow on mobile for major pages.
- No JS console errors on baseline routes during core interactions.

## 7) Change Safety Rules For Phase 1-2
- Do not rename or remove selector-contract IDs/classes.
- Move inline styles to classes gradually, one page group at a time.
- Keep visual updates isolated from behavior updates.
- Validate each page group immediately after edits, not at the end.

## 8) Suggested Execution Order For UI Upgrade (After Phase 0)
1. Base shell (`base.html` + nav/footer + tokens)
2. Read-only pages (home, terms, privacy)
3. Report pages
4. Dashboard
5. Camera-heavy flows (client log, add/edit client, admin signup/face login) last

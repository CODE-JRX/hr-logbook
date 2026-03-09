# Phase 5 Release Checklist

Date: __________
Owner: __________

## 1) Performance Validation
- [ ] Home first slide loads immediately and without visual delay
- [ ] Non-visible carousel slides lazy-load
- [ ] Footer logo is lazy-loaded
- [ ] Dashboard admin profile image lazy-loads
- [ ] No broken image rendering in light and dark themes

## 2) UX Regression Validation
- [ ] Navigation works for guest and admin states
- [ ] Theme toggle persists after refresh
- [ ] Camera flow works on `/client-log`
- [ ] Add Client 3-angle capture works
- [ ] Edit Client 3-angle capture works
- [ ] Admin Signup 3-angle capture works
- [ ] Admin Face Login + PIN flow works

## 3) Accessibility Validation
- [ ] Keyboard-only navigation reaches nav, controls, and modals
- [ ] Focus ring is clearly visible on interactive elements
- [ ] Reduced motion preference removes non-essential animations
- [ ] Message overlays announce updates to assistive tech

## 4) Browser/Viewport Validation
- [ ] Desktop (1440x900): key routes visually stable
- [ ] Mobile (390x844): no horizontal overflow on key routes
- [ ] Critical pages tested in at least 2 browsers

## 5) Deployment Readiness
- [ ] `docs/uiux/phase-0-checklist.md` marked complete
- [ ] `docs/uiux/phase-1` to `phase-5` notes reviewed
- [ ] Final UI/UX sign-off recorded

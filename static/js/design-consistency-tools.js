// Design Consistency Tools for HRMO Logbook
// Add this script to your base.html template before </body>

(function() {
  'use strict';

  // =================================================================
  // DESIGN CONSISTENCY CHECKLIST
  // =================================================================
  /*
  DESIGN CONSISTENCY CHECKLIST:

  COLOR PALETTE:
  □ All buttons use --primary-color or --secondary-color
  □ All links use --primary-color for hover states
  □ No hardcoded colors (except in fallbacks)
  □ Dark mode colors are properly defined

  TYPOGRAPHY:
  □ All headings use h1-h6 elements or design system classes
  □ Body text uses --font-family
  □ Font sizes follow the scale (--font-size-h1 through --font-size-caption)
  □ Line heights are consistent (1.2-1.6)

  SPACING:
  □ Margins use --spacing-* variables
  □ Padding uses --spacing-* variables
  □ No arbitrary spacing values (4px, 8px, etc.)

  COMPONENTS:
  □ All buttons use .btn-primary, .btn-secondary, or new variants
  □ All forms use .form-control or new form classes
  □ All cards use .card or .card-new
  □ No inline styles for layout/color properties

  RESPONSIVE:
  □ Breakpoints use consistent media queries
  □ Mobile layouts work properly
  □ No horizontal scrolling on mobile

  ACCESSIBILITY:
  □ Color contrast meets WCAG standards
  □ Focus states are visible
  □ Alt text on images
  □ Semantic HTML structure

  PERFORMANCE:
  □ No unused CSS classes
  □ CSS is minified in production
  □ Critical CSS is inlined
  */

  // =================================================================
  // BROWSER EXTENSIONS FOR DESIGN AUDITS
  // =================================================================
  /*
  BROWSER EXTENSIONS FOR DESIGN AUDITS:

  CHROME/EDGE:
  - "CSS Overview" - Analyze CSS usage and find inconsistencies
  - "Lighthouse" - Built-in audit tool for design and performance
  - "Stark" - Accessibility and contrast checking
  - "Color Contrast Analyzer" - Check color accessibility

  FIREFOX:
  - "Web Developer Toolbar" - CSS analysis and debugging
  - "Accessibility Inspector" - Built-in accessibility checks
  - "ColorZilla" - Color picker and analysis

  GENERAL:
  - "WAVE Evaluation Tool" - Web accessibility evaluation
  - "Siteimprove Accessibility Checker" - Comprehensive accessibility audit
  - "Contrast Checker" - Simple color contrast verification
  */

  // =================================================================
  // JAVASCRIPT CONSOLE LOGGER: Log Design Inconsistencies
  // =================================================================

  // Log design inconsistencies to console
  function logInconsistency(message, element) {
    console.warn('🎨 Design Inconsistency:', message, element);
  }

  // Check for hardcoded colors
  function checkHardcodedColors() {
    const elements = document.querySelectorAll('[style*="color"], [style*="background"]');
    elements.forEach(el => {
      const style = el.getAttribute('style');
      if (style && !style.includes('var(--') && (style.includes('#') || style.includes('rgb'))) {
        logInconsistency('Hardcoded color found', el);
      }
    });
  }

  // Check for non-design-system buttons
  function checkButtons() {
    const buttons = document.querySelectorAll('button:not(.btn-primary):not(.btn-secondary):not(.btn-primary-new):not(.btn-secondary-new)');
    buttons.forEach(btn => {
      if (!btn.classList.contains('btn')) {
        logInconsistency('Button not using design system', btn);
      }
    });
  }

  // Check for non-design-system forms
  function checkForms() {
    const inputs = document.querySelectorAll('input:not(.form-control):not(.form-input-new), select:not(.form-control), textarea:not(.form-control)');
    inputs.forEach(input => {
      logInconsistency('Form element not using design system', input);
    });
  }

  // Check for inconsistent spacing
  function checkSpacing() {
    const elements = document.querySelectorAll('[style*="margin"], [style*="padding"]');
    elements.forEach(el => {
      const style = el.getAttribute('style');
      if (style && !style.includes('var(--spacing') && /\d+px/.test(style)) {
        logInconsistency('Hardcoded spacing found', el);
      }
    });
  }

  // Run all checks
  function runConsistencyChecks() {
    console.log('🔍 Running design consistency checks...');
    checkHardcodedColors();
    checkButtons();
    checkForms();
    checkSpacing();
    console.log('✅ Design consistency checks complete');
  }

  // =================================================================
  // DEBUG MODE ACTIVATION
  // =================================================================

  // Create debug toggle button
  function createDebugToggle() {
    const toggle = document.createElement('button');
    toggle.id = 'debug-toggle';
    toggle.textContent = '🔍 Debug';
    toggle.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      padding: 10px;
      background: #ff6b6b;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    `;

    toggle.addEventListener('click', function() {
      document.body.classList.toggle('debug-mode');
      this.textContent = document.body.classList.contains('debug-mode') ? '🔍 Debug ON' : '🔍 Debug OFF';
    });

    document.body.appendChild(toggle);
  }

  // Run on page load
  window.addEventListener('load', function() {
    runConsistencyChecks();
    createDebugToggle();
  });

  // Expose for manual running
  window.checkDesignConsistency = runConsistencyChecks;

  console.log('🎨 Design consistency tools loaded. Run checkDesignConsistency() to check current page.');
})();

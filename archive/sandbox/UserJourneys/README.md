User Journeys — Demo & quick script

This README explains how to preview the new light, card-based white-theme for the sandbox/UserJourneys area and provides a short demo script.

Files changed
- styles.css — replaced with a light, card-based theme (this file).

How to preview
1. Open sandbox/UserJourneys/index.html (or the relevant HTML demo page) in a browser. If there is no index.html, create a simple preview file using the snippet below.
2. Ensure the page includes a reference to ./styles.css in the head:

   <link rel="stylesheet" href="./styles.css">

Quick demo HTML (create sandbox/UserJourneys/preview.html if needed)

<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>User Journeys — Preview</title>
    <link rel="stylesheet" href="./styles.css">
  </head>
  <body>
    <div class="uj-container">
      <div class="uj-hero">
        <div>
          <h1 class="uj-hero__title">User Journeys — Cards Preview</h1>
          <p class="uj-hero__desc">Light, accessible card-based layout for journey steps and interactions.</p>
        </div>
        <div class="u-center">
          <button class="btn btn--primary">Primary action</button>
        </div>
      </div>

      <div class="card">
        <h3 class="card__title">Sign-up flow</h3>
        <div class="card__meta">Example step list</div>
        <div class="card__body">
          <ul class="steps">
            <li class="step"><div class="step__num">1</div><div><strong>Create account</strong><div class="text-muted">Enter email and password</div></div></li>
            <li class="step"><div class="step__num">2</div><div><strong>Verify email</strong><div class="text-muted">Use OTP or verification link</div></div></li>
            <li class="step"><div class="step__num">3</div><div><strong>Onboarding</strong><div class="text-muted">Quick setup steps</div></div></li>
          </ul>
        </div>
        <div class="card__footer">
          <button class="btn btn--primary">Start</button>
          <button class="btn btn--ghost">Learn more</button>
        </div>
      </div>

      <div class="card card--compact">
        <h4 class="card__title">Compact card</h4>
        <div class="card__meta">Used for small widgets</div>
        <div class="card__body">Short content and actions.</div>
      </div>
    </div>
  </body>
</html>

Demo script (manual)
- Step 1: Open the preview page in desktop and mobile widths (devtools) and verify cards reflow.
- Step 2: Check interactive elements (buttons, inputs) are reachable via keyboard (Tab) and show focus outlines.
- Step 3: Verify text contrast against the background. Use browser devtools or an accessibility extension to confirm.
- Step 4: If you have the original sandbox behavior, compare spacing and shadow changes; the visual intent should be a light, airy card system with mild elevation.

Notes
- The stylesheet uses CSS variables for quick color tweaking.
- If you need a dark-theme counterpart, copy variables in :root and create a .dark-mode selector to override them.

If you want any adjustments (colors, radius, spacing, or a dark-mode variant), tell me what to change and I will update the files.
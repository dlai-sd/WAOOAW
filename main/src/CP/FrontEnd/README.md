# CP Frontend

Customer-facing UI for WAOOAW agent marketplace.

## Tech Stack

- HTML5, CSS3, Modern JavaScript
- Optional: React (if needed for complex state management)
- Design: Dark theme (#0a0a0a), neon accents (#00f2fe, #667eea)

## Directory Structure (To Be Created)

```
FrontEnd/
├── index.html              # Landing page
├── marketplace.html        # Agent marketplace
├── agent-detail.html       # Agent detail page
├── trial-signup.html       # Trial signup flow
├── dashboard.html          # Customer dashboard
├── css/
│   ├── variables.css       # Design tokens
│   ├── components.css      # Reusable components
│   └── pages.css           # Page-specific styles
├── js/
│   ├── api.js              # Backend API calls
│   ├── marketplace.js      # Marketplace logic
│   └── utils.js            # Helper functions
├── assets/
│   ├── images/             # Logos, icons
│   └── fonts/              # Space Grotesk, Outfit, Inter
└── package.json            # NPM dependencies (if using build tools)
```

## Design System

See `/docs/BRAND_STRATEGY.md` for:
- Colors: Dark theme with neon accents
- Fonts: Space Grotesk (display), Outfit (headings), Inter (body)
- Vibe: Marketplace-focused (Upwork meets cutting-edge AI)

## Key Pages

1. **Landing**: Hero + value prop + CTA
2. **Marketplace**: Agent cards with search/filters
3. **Agent Detail**: Full profile + demo + trial signup
4. **Dashboard**: Manage subscriptions, agents, billing

## Getting Started

```bash
# Install dependencies (if using build tools)
npm install

# Run local dev server
npm run dev

# Build for production
npm run build
```

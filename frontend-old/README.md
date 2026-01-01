# Archived: Original Vanilla JS Portal

**Archived Date**: January 1, 2026  
**Reason**: Replaced by Reflex-based PlatformPortal/  
**Reference**: docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md

## What's Here

Original operational portal built with:
- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework)
- **Features**: 8 pages, OAuth2, theme system, mock data
- **Status**: Working but unmaintainable

### Pages
- portal.html - Dashboard
- login.html - Google OAuth2
- agents.html - Agent listing
- events.html - Event viewer
- metrics.html - Metrics dashboard
- logs.html - Log viewer
- diagnostics.html - System diagnostics
- alerts.html - Alert management

## Why Replaced?

**Challenges**:
- No framework = code duplication
- Hard to maintain and extend
- No state management
- No reusable components
- Team wants pure Python stack

**New Approach**:
- **Reflex** - Pure Python frontend
- Component-based architecture
- Built-in WebSocket, state management
- 100% Python (no JS required)
- 14 stories, 246 points, 14 weeks

## What Was Kept?

- ✅ Theme colors (theme.css) - adapted to Reflex
- ✅ OAuth2 (backend/app/auth/oauth.py) - integrated
- ✅ Branding assets (logo, favicon) - moved to PlatformPortal/

## Historical Context

This was commit **ca20352** - the "clean" portal state.
Kept for reference but not maintained going forward.

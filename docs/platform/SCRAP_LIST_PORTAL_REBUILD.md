# Scrap List - Portal Rebuild (Reflex Migration)

**Date**: January 1, 2026  
**Context**: Moving from vanilla HTML/CSS/JS portal to Reflex (Pure Python)  
**Reference**: PLATFORM_PORTAL_MASTER_PLAN.md

---

## 🗑️ Items to Archive/Scrap

### Category 1: Current Portal Code (Vanilla JS) - **TO ARCHIVE**

#### Action: Move to `frontend-old/` folder

**Portal HTML Pages** (8 files):
- ✅ `frontend/portal.html` - Main dashboard
- ✅ `frontend/login.html` - Login page with OAuth2
- ✅ `frontend/agents.html` - Agent listing (mock data)
- ✅ `frontend/events.html` - Event viewer
- ✅ `frontend/metrics.html` - Metrics dashboard
- ✅ `frontend/logs.html` - Log viewer
- ✅ `frontend/diagnostics.html` - System diagnostics
- ✅ `frontend/alerts.html` - Alert management
- ✅ `frontend/auth/callback.html` - OAuth callback handler

**Portal CSS Files** (7 files):
- ✅ `frontend/css/portal.css` - Portal-specific styles
- ✅ `frontend/css/agents.css` - Agent page styles
- ✅ `frontend/css/events.css` - Events page styles
- ✅ `frontend/css/metrics.css` - Metrics page styles
- ✅ `frontend/css/logs.css` - Logs page styles
- ✅ `frontend/css/diagnostics.css` - Diagnostics page styles
- ✅ `frontend/css/alerts.css` - Alerts page styles

**Portal JavaScript Files** (7 files):
- ✅ `frontend/js/portal.js` - Portal main logic
- ✅ `frontend/js/agents.js` - Agent page logic
- ✅ `frontend/js/events.js` - Events page logic
- ✅ `frontend/js/metrics.js` - Metrics page logic
- ✅ `frontend/js/logs.js` - Logs page logic
- ✅ `frontend/js/diagnostics.js` - Diagnostics page logic
- ✅ `frontend/js/alerts.js` - Alerts page logic

**Support Files** (2 files):
- ✅ `frontend/package.json` - Node dependencies (eslint, prettier)
- ✅ `frontend/.eslintrc.json` - ESLint config for JS

**Total**: 25 files to archive

---

### Category 2: Files to KEEP (Will be adapted/integrated)

**Theme System** - Keep and adapt for Reflex:
- 🔄 `frontend/css/theme.css` - WAOOAW colors (#0a0a0a, #00f2fe, #667eea)
- 🔄 `frontend/js/theme-manager.js` - Dark/light theme logic
  - **Action**: Extract theme values, port logic to Reflex state

**OAuth2 Integration** - Keep and adapt:
- 🔄 `backend/app/auth/oauth.py` - Working Google OAuth2
  - **Action**: Integrate with Reflex authentication

**Branding Assets** - Keep as-is:
- ✅ `frontend/assets/Waooaw-Logo.png` - Logo (will move to PlatformPortal/)
- ✅ `frontend/assets/favicon.ico` - Favicon (will move to PlatformPortal/)

**Backend APIs** - Keep and enhance:
- ✅ `backend/app/main.py` - FastAPI with platform endpoints
  - **Action**: Add new endpoints for 14 stories

---

### Category 3: Planning Documents - **SUPERSEDED**

**Epic Documents** (2 files):
- 📋 `docs/platform/EPIC_4.1_MAINTENANCE_PORTAL.md` - Empty file, originally planned maintenance portal
  - **Status**: Superseded by PLATFORM_PORTAL_MASTER_PLAN.md
  - **Action**: Delete (empty anyway)

- 📋 `docs/platform/epics/EPIC_5.1_OPERATIONAL_PORTAL.md` - Original Epic 5.1 (7 stories, 102 points)
  - **Status**: Superseded by PLATFORM_PORTAL_MASTER_PLAN.md
  - **Action**: Archive to `docs/platform/archive/`

**Execution Plans** (1 file):
- 📋 `docs/platform/EXECUTION_PLAN_EPIC_5.1.md` - Original 225-point plan (extended version)
  - **Status**: Superseded by PLATFORM_PORTAL_MASTER_PLAN.md (246 points, Reflex-based)
  - **Action**: Archive to `docs/platform/archive/`

**Story Documents** - **KEEP** (will reference these):
- ✅ `docs/platform/stories/STORY_5.1.0_COMMON_PLATFORM_COMPONENTS.md` (13 pts)
- ✅ `docs/platform/stories/STORY_5.1.7_CONTEXT_OBSERVABILITY.md` (21 pts)
- ✅ `docs/platform/stories/STORY_5.1.8_REALTIME_MESSAGE_QUEUE_MONITORING.md` (13 pts)
- ✅ `docs/platform/stories/STORY_5.1.9_REALTIME_ORCHESTRATION_MONITORING.md` (16 pts)
- ✅ `docs/platform/stories/STORY_5.1.10_AGENT_FACTORY_MODE.md` (34 pts)
- ✅ `docs/platform/stories/STORY_5.1.11_AGENT_SERVICING_MODE.md` (55 pts)
- ✅ `docs/platform/stories/STORY_5.1.12_TECHNICAL_HELPDESK_MODE.md` (34 pts)
  - **Action**: Keep - developers will implement these in Reflex

**Total**: 3 files to archive

---

### Category 4: Marketplace/Marketing Pages - **KEEP**

These are NOT part of the portal - they're public-facing marketing pages:
- ✅ `frontend/index.html` - Homepage
- ✅ `frontend/marketplace.html` - Agent marketplace
- ✅ `frontend/about.html` - About page
- ✅ `frontend/pricing.html` - Pricing page
- ✅ `frontend/contact.html` - Contact page
- ✅ `frontend/blog.html` - Blog page
- ✅ `frontend/css/marketplace.css` - Marketplace styles
- ✅ `frontend/css/style.css` - Main site styles
- ✅ `frontend/js/script.js` - Main site JS

**Action**: NO CHANGE - These serve the public marketplace, not the operator portal

---

### Category 5: Test/Legacy Files - **TO REMOVE**

- 🗑️ `frontend/index-old-v2.html` - Old homepage version
- 🗑️ `frontend/test_agents.html` - Test page
- 🗑️ `frontend/test_nav.html` (if exists) - Test navigation
- 🗑️ `frontend/css/style-old.css` - Old styles

**Action**: Delete (obsolete test files)

---

## 📋 Summary Statistics

| Category | Files | Action |
|----------|-------|--------|
| Portal Code (HTML/CSS/JS) | 25 | Archive to `frontend-old/` |
| Theme System | 2 | Keep & adapt to Reflex |
| OAuth Integration | 1 | Keep & integrate with Reflex |
| Branding Assets | 2 | Keep & move to PlatformPortal/ |
| Backend APIs | 1 | Keep & enhance |
| Planning Documents | 3 | Archive to `docs/platform/archive/` |
| Story Documents | 7 | **KEEP** - implementation guides |
| Marketplace Pages | 9 | **KEEP** - not portal related |
| Test/Legacy Files | 4 | Delete |
| **NEW - Master Plan** | 1 | **ACTIVE** - PLATFORM_PORTAL_MASTER_PLAN.md |

**Total to Archive**: 28 files  
**Total to Delete**: 4 files  
**Total to Keep**: 20 files  
**New Files**: 1 file (master plan)

---

## 🎯 Recommended Git Housekeeping Steps

### Step 1: Create Archive Folders
```bash
mkdir -p frontend-old
mkdir -p docs/platform/archive
```

### Step 2: Archive Portal Code
```bash
# Move portal HTML pages
mv frontend/portal.html frontend-old/
mv frontend/login.html frontend-old/
mv frontend/agents.html frontend-old/
mv frontend/events.html frontend-old/
mv frontend/metrics.html frontend-old/
mv frontend/logs.html frontend-old/
mv frontend/diagnostics.html frontend-old/
mv frontend/alerts.html frontend-old/
mv frontend/auth frontend-old/

# Move portal CSS files
mkdir -p frontend-old/css
mv frontend/css/portal.css frontend-old/css/
mv frontend/css/agents.css frontend-old/css/
mv frontend/css/events.css frontend-old/css/
mv frontend/css/metrics.css frontend-old/css/
mv frontend/css/logs.css frontend-old/css/
mv frontend/css/diagnostics.css frontend-old/css/
mv frontend/css/alerts.css frontend-old/css/

# Move portal JS files
mkdir -p frontend-old/js
mv frontend/js/portal.js frontend-old/js/
mv frontend/js/agents.js frontend-old/js/
mv frontend/js/events.js frontend-old/js/
mv frontend/js/metrics.js frontend-old/js/
mv frontend/js/logs.js frontend-old/js/
mv frontend/js/diagnostics.js frontend-old/js/
mv frontend/js/alerts.js frontend-old/js/

# Move JS tooling
mv frontend/package.json frontend-old/
mv frontend/.eslintrc.json frontend-old/
```

### Step 3: Archive Old Planning Documents
```bash
# Archive superseded epic/execution documents
mv docs/platform/EPIC_4.1_MAINTENANCE_PORTAL.md docs/platform/archive/
mv docs/platform/epics/EPIC_5.1_OPERATIONAL_PORTAL.md docs/platform/archive/
mv docs/platform/EXECUTION_PLAN_EPIC_5.1.md docs/platform/archive/

# Add README to archive explaining what's there
cat > docs/platform/archive/README.md << 'EOF'
# Archived Portal Planning Documents

These documents were superseded by **PLATFORM_PORTAL_MASTER_PLAN.md** (January 1, 2026).

## Contents

- `EPIC_4.1_MAINTENANCE_PORTAL.md` - Empty original maintenance portal epic
- `EPIC_5.1_OPERATIONAL_PORTAL.md` - Original operational portal epic (102 points)
- `EXECUTION_PLAN_EPIC_5.1.md` - Original execution plan (225 points, React-based)

## Why Archived?

Decision made to rebuild portal with **Reflex (Pure Python)** instead of React/TypeScript.
All planning consolidated into single master plan (246 points, 14 weeks, 5 phases).

See: `/docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md`
EOF
```

### Step 4: Delete Test/Legacy Files
```bash
# Remove obsolete test files
rm frontend/index-old-v2.html
rm frontend/test_agents.html
rm frontend/css/style-old.css
# rm frontend/test_nav.html  # if exists
```

### Step 5: Create Commit
```bash
git add -A
git commit -m "chore: archive old portal code for Reflex rebuild

- Archived vanilla JS portal (25 files) to frontend-old/
- Archived superseded planning docs to docs/platform/archive/
- Deleted obsolete test files
- Kept: theme system, OAuth, story docs, marketplace pages

Preparing for new PlatformPortal/ build with Reflex (Python).
See: docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md"
```

### Step 6: Create README in frontend-old/
```bash
cat > frontend-old/README.md << 'EOF'
# Archived: Original Vanilla JS Portal

**Archived Date**: January 1, 2026  
**Reason**: Replaced by Reflex-based PlatformPortal/  
**Reference**: PLATFORM_PORTAL_MASTER_PLAN.md

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
EOF
```

---

## ✅ Checklist for Housekeeping

- [ ] Review this scrap list with team
- [ ] Create backup branch before archiving: `git checkout -b backup/vanilla-portal-ca20352`
- [ ] Create archive folders (`frontend-old/`, `docs/platform/archive/`)
- [ ] Move portal code (25 files) to `frontend-old/`
- [ ] Move old planning docs (3 files) to `docs/platform/archive/`
- [ ] Delete test/legacy files (4 files)
- [ ] Create READMEs in archive folders
- [ ] Commit changes with descriptive message
- [ ] Tag commit: `git tag -a v0.9.0-portal-archived -m "Archived vanilla portal before Reflex rebuild"`
- [ ] Push: `git push origin main --tags`
- [ ] Verify kept files still work:
  - [ ] Marketplace pages load correctly
  - [ ] Backend API still responds
  - [ ] Theme system files accessible
- [ ] Ready to create `PlatformPortal/` folder structure

---

## 🚀 Next Steps After Housekeeping

1. **Create PlatformPortal/ folder**:
   ```bash
   mkdir PlatformPortal
   cd PlatformPortal
   pip install reflex
   reflex init
   ```

2. **Setup project structure** (see PLATFORM_PORTAL_MASTER_PLAN.md Section 📁)

3. **Configure WAOOAW theme** - Extract colors from theme.css:
   ```python
   # PlatformPortal/theme/colors.py
   WAOOAW_COLORS = {
       "bg_black": "#0a0a0a",
       "bg_gray": "#18181b",
       "neon_cyan": "#00f2fe",
       "neon_purple": "#667eea",
       "neon_pink": "#f093fb",
       # ... etc
   }
   ```

4. **Port OAuth2** - Integrate backend/app/auth/oauth.py with Reflex auth

5. **Begin Story 5.1.0** - Common Components (Week 1-2, 13 points)

---

**Document Status**: ✅ Ready for Review  
**Approved By**: _________  
**Date Approved**: _________  
**Action Date**: January 2, 2026 (after approval)

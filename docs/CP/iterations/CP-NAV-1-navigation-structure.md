# CP-NAV-1 — CP Web Navigation Structure

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-NAV-1` |
| Feature area | Customer Portal — Navigation Structure |
| Created | 2026-03-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CP/navigation-ux-analysis.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 5 |
| Total stories | 7 |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — wire sidebar nav to new UX structure | 3 | 4 | 2h | 2026-03-01 12:00 UTC |
| 2 | Lane A — Edit Profile (backend + CP FE + mobile nav) | 2 | 3 | 3h | 2026-03-01 15:00 UTC |

---

## Agent Execution Rules

### Rule 0 — Branch
```bash
git checkout main && git pull
git checkout -b feat/CP-NAV-1-it1-e1
```

### Rule 1 — Scope lock
Implement exactly the acceptance criteria. Do not refactor unrelated code.

### Rule 2 — Tests before next story
Write tests listed in the story card. Run `cd src/CP/FrontEnd && npm run test:run`.

### Rule 3 — STUCK PROTOCOL
If blocked 3 times: commit WIP, open draft PR, HALT.

### Rule 4 — Iteration PR when all epics done
```bash
gh pr create --base main --title "feat(CP-NAV-1): iteration 1 — navigation structure" --body "..."
```

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | New page stubs | Create CommandCentre, Deliverables, Inbox, ProfileSettings pages | 🟢 Done | — |
| E2-S1 | 1 | Sidebar nav redesign | Update AuthenticatedPortal sidebar menu items | 🟢 Done | — |
| E2-S2 | 1 | Sidebar nav redesign | Wire Discover nav item to /discover route | 🟢 Done | — |
| E3-S1 | 1 | Navigation tests | Add AuthenticatedPortal navigation tests | 🟢 Done | — |
| E4-S1 | 2 | Edit Profile backend | Add GET + PATCH /api/cp/profile to CP BackEnd | 🟢 Done | — |
| E4-S2 | 2 | Edit Profile CP FE | Wire Edit Profile modal in ProfileSettings | 🟢 Done | — |
| E5-S1 | 2 | Mobile profile nav | Create EditProfileScreen + wire ProfileScreen navigation | 🟢 Done | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Navigation Structure

**Scope:** Authenticated users see the 8-item sidebar nav defined in the UX analysis (Command Centre, My Agents, Discover, Goals, Deliverables, Inbox, Subscriptions & Billing, Profile & Settings).
**Lane:** A — pure frontend wiring, no new backend endpoints
**⏱ Estimated:** 2h | **Come back:** 2026-03-01 12:00 UTC
**Epics:** E1, E2, E3

### Dependency Map

```
E1-S1 ──► E2-S1 ──► E2-S2
E3-S1 (after E2-S2)
```

---

### Epic E1: New page stubs

**Branch:** `feat/CP-NAV-1-it1-e1`
**User story:** As an authenticated customer, I can navigate to Command Centre, Deliverables, Inbox, and Profile & Settings, so that the sidebar has destinations for all 8 nav items.

#### Story E1-S1: Create stub pages for new nav destinations

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/CP-NAV-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
Create four new page components in `src/CP/FrontEnd/src/pages/authenticated/`:
- `CommandCentre.tsx` — evolves from Dashboard.tsx; heading "Command Centre", same live activity feed
- `Deliverables.tsx` — stub with heading "Deliverables" and placeholder content
- `Inbox.tsx` — stub with heading "Inbox" and placeholder content
- `ProfileSettings.tsx` — stub with heading "Profile & Settings" and placeholder content

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` | 1–97 | Structure to clone for CommandCentre |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` | create | Clone of Dashboard with heading "Command Centre" |
| `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx` | create | Stub page |
| `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx` | create | Stub page |
| `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx` | create | Stub page |

**Acceptance criteria:**
1. All four files exist and export a default React component
2. Each component renders an `<h1>` with the correct page title

**Commit message:** `feat(CP-NAV-1): add CommandCentre, Deliverables, Inbox, ProfileSettings stubs`

---

### Epic E2: Sidebar nav redesign

**Branch:** `feat/CP-NAV-1-it1-e2`
**User story:** As an authenticated customer, I see 8 nav items in the sidebar matching the UX analysis, so I can navigate the full portal.

#### Story E2-S1: Update AuthenticatedPortal sidebar menu items

**BLOCKED UNTIL:** E1-S1 done
**Estimated time:** 30 min
**Branch:** `feat/CP-NAV-1-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
Update `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`:
- Replace `Page` type with: `'command-centre' | 'my-agents' | 'goals' | 'deliverables' | 'inbox' | 'billing' | 'profile-settings'`
- Replace `menuItems` with 7 items (Discover is handled separately as external nav)
- Update `renderPage()` to use new page components
- Import new page components (CommandCentre, Deliverables, Inbox, ProfileSettings)
- Remove imports of Approvals and Performance (no longer in nav)

**Acceptance criteria:**
1. Sidebar renders exactly 7 internal items + Discover (navigates to /discover)
2. Command Centre is the default landing page
3. Old items (Approvals, Performance, Mobile App, Notifications, Help) are gone

**Commit message:** `feat(CP-NAV-1): redesign sidebar nav to match UX analysis`

#### Story E2-S2: Wire Discover nav item to /discover route

**BLOCKED UNTIL:** E2-S1 done
**Estimated time:** 15 min
**Branch:** `feat/CP-NAV-1-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
Add "Discover" as a sidebar item that calls `useNavigate('/discover')` instead of switching the internal page state.

**Acceptance criteria:**
1. Clicking "Discover" in the sidebar navigates to `/discover` (not swaps page content)
2. No in-portal page is rendered for Discover

**Commit message:** `feat(CP-NAV-1): Discover sidebar item navigates to /discover route`

---

### Epic E3: Navigation tests

**Branch:** `feat/CP-NAV-1-it1-e3`
**User story:** As a developer, I have tests confirming the new navigation renders all 8 sidebar items correctly.

#### Story E3-S1: Add AuthenticatedPortal navigation tests

**BLOCKED UNTIL:** E2-S2 done
**Estimated time:** 30 min
**Branch:** `feat/CP-NAV-1-it1-e3`
**CP BackEnd pattern:** N/A

**Acceptance criteria:**
1. Test renders AuthenticatedPortal and finds "Command Centre" in sidebar
2. Test renders and finds "Deliverables", "Inbox", "Subscriptions & Billing", "Profile & Settings"
3. Test confirms "Discover" item is present

**Test command:**
```bash
cd src/CP/FrontEnd && npm run test:run -- src/__tests__/AuthenticatedPortal.test.tsx
```

**Commit message:** `feat(CP-NAV-1): add AuthenticatedPortal navigation tests`

---

## Iteration 2 — Edit Profile

**Scope:** Authenticated users can edit their profile (full name, phone, business, industry) via CP web and navigate to Edit Profile in the mobile app.
**Lane:** A (CP web) + B (new backend endpoint)
**⏱ Estimated:** 3h | **Come back:** 2026-03-01 15:00 UTC
**Epics:** E4, E5

### Dependency Map

```
E4-S1 ──► E4-S2
E5-S1 (independent)
```

---

### Epic E4: Edit Profile

**Branch:** `feat/CP-NAV-1-it2`
**User story:** As an authenticated customer, I can edit my profile (name, phone, business) so my details stay accurate.

#### Story E4-S1: Add GET + PATCH /api/cp/profile backend endpoint

**BLOCKED UNTIL:** none
**Estimated time:** 45 min

**What to do:**
- Extend `User` model with `full_name`, `phone`, `business_name`, `industry` (all Optional)
- Add `update_profile(user_id, updates)` to `UserStore`
- Create `src/CP/BackEnd/api/cp_profile.py` with `GET /cp/profile` and `PATCH /cp/profile`
- Register router in `main.py`
- Add `tests/test_cp_profile_routes.py`

**Acceptance criteria:**
1. `GET /api/cp/profile` returns 200 with profile fields for authenticated user
2. `PATCH /api/cp/profile` with `{"full_name": "Alice"}` returns 200 with updated full_name
3. Both endpoints return 401 for unauthenticated requests

**Commit message:** `feat(CP-NAV-1): add GET + PATCH /api/cp/profile endpoint`

#### Story E4-S2: Wire Edit Profile modal in ProfileSettings

**BLOCKED UNTIL:** E4-S1 done
**Estimated time:** 45 min

**What to do:**
- Create `src/CP/FrontEnd/src/services/profile.service.ts`
- Update `ProfileSettings.tsx` to open an edit modal on "Edit Profile" click
- Form fields: full_name, phone, business_name, industry
- Show loading / error / success states

**Acceptance criteria:**
1. Clicking "Edit Profile" opens a modal with four input fields
2. Saving calls `PATCH /api/cp/profile` and closes the modal on success
3. Error message shown if save fails

**Commit message:** `feat(CP-NAV-1): wire Edit Profile modal in ProfileSettings`

---

### Epic E5: Mobile Profile Navigation

**Branch:** `feat/CP-NAV-1-it2`
**User story:** As a mobile user, I can tap "Edit Profile" in the Profile tab and land on an editable form.

#### Story E5-S1: Create EditProfileScreen and wire ProfileScreen navigation

**BLOCKED UNTIL:** none
**Estimated time:** 45 min

**What to do:**
- Create `src/mobile/src/screens/profile/EditProfileScreen.tsx`
- Export from `screens/profile/index.ts`
- Register `EditProfile` screen in `MainNavigator.tsx` ProfileNavigator
- Update `ProfileScreen.tsx` to `navigation.navigate('EditProfile')` on "Edit Profile" tap

**Acceptance criteria:**
1. Tapping "Edit Profile" navigates to EditProfileScreen (not empty `() => {}`)
2. EditProfileScreen has form fields and a "Save Changes" button
3. Back navigation works

**Commit message:** `feat(CP-NAV-1): create EditProfileScreen and wire mobile profile navigation`

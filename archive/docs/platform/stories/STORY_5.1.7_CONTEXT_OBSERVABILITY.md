# Story 5.1.7: Context-Based Observability (Agent-Specific Views)

**Story ID**: 5.1.7  
**Epic**: Epic 5.1 - Operational Portal  
**Priority**: P1  
**Points**: 8  
**Status**: Ready for Development  
**Dependencies**: Story 5.1.0 (Common Platform Components - Context Selector, Status Badge)  
**Risk**: Low

---

## User Story

**As a** platform operator  
**I want** to see logs/alerts/events/metrics filtered by selected agent  
**So that** I can troubleshoot specific agents without noise from the entire platform

---

## Problem Statement

### Current State
- Logs page shows ALL platform logs (14 agents mixed together)
- Alerts page shows ALL alerts (hard to find agent-specific issues)
- Events page shows ALL events (overwhelming when debugging)
- No way to say "show me only WowMemory's logs"
- Must manually search/filter every time
- Context lost when switching between pages

### User Pain Points
1. "WowMemory crashed, but I see 1000 logs from all agents"
2. "Which alert belongs to WowCache? I have to read each one"
3. "Deployed WowDomain, but can't see just its deployment logs"
4. "Switching from Agents → Logs → Alerts loses my focus agent"

---

## Proposed Solution

### Context Switcher Architecture

**Global Context State:**
```
User selects agent → Context = "WowMemory"
  ↓
All pages filter to WowMemory:
  • Logs page → Only WowMemory logs
  • Alerts page → Only WowMemory alerts
  • Events page → Only WowMemory events
  • Metrics page → Only WowMemory metrics
  • Diagnostics → Only WowMemory health

User clicks "Platform-Wide" → Context = null
  ↓
All pages show aggregate data from all 14 agents
```

### Key Features

1. **Context Selector in Header**
   - Dropdown: "Platform-Wide" or any of 14 agents
   - Persists in localStorage across page refreshes
   - Visual indicator shows current context

2. **Quick Action Buttons on Agent Cards**
   - Click agent → Sets context
   - "📝 Logs" button → Switch context + navigate to logs
   - "🚨 Alerts" button → Switch context + navigate to alerts

3. **Auto-Context Switching**
   - Deploy agent → Auto-switch to that agent + show logs
   - Agent errors → Notification links to agent context
   - Bulk operations → Keep platform-wide context

4. **Context Banner on Filtered Pages**
   - "Viewing logs for: WowMemory [View All]"
   - Clear visual indicator when filtered
   - One-click to clear filter

---

## User Flows

### Flow 1: Manual Context Selection
```
1. User on agents.html
2. User clicks context dropdown → Selects "WowMemory"
3. Header shows: "Viewing: WowMemory"
4. User navigates to logs.html
5. Page loads showing only WowMemory logs
6. User navigates to alerts.html  
7. Page shows only WowMemory alerts
```

### Flow 2: Quick Action from Agent Card
```
1. User on agents.html
2. User clicks "📝 Logs" button on WowMemory card
3. Context auto-switches to WowMemory
4. Browser navigates to logs.html
5. Logs page shows only WowMemory logs
6. Context persists if user navigates to alerts.html
```

### Flow 3: Auto-Switch on Agent Action
```
1. User clicks "Deploy WowMemory"
2. Context auto-switches to WowMemory
3. Logs page auto-opens showing deployment progress
4. User sees real-time: "Pulling image...", "Starting...", "Healthy"
5. Context remains on WowMemory for troubleshooting
```

### Flow 4: Error Notification Link
```
1. WowMemory crashes → Toast notification appears
2. User clicks notification
3. Context switches to WowMemory
4. Agents page shows error panel for WowMemory
5. "View Logs" button opens logs with WowMemory context
```

---

## Technical Implementation

### Frontend Components

**1. AppContext State Manager** (`js/context-manager.js`)
- Global state: `currentAgent` (null or agent_id)
- Methods: `setContext()`, `getContext()`, `clearContext()`
- Persistence: localStorage with key `waooaw_context`
- Pub/sub: Notify listeners on context change
- Auto-reload current page data when context changes

**2. Context Selector UI** (header in all pages)
- Dropdown with all 14 agents
- "Platform-Wide" default option
- "Clear Filter" button
- Updates on context change via subscription

**3. Context Indicator Banner** (shows when filtered)
- "Viewing: [Agent Name]" badge
- Dismissable with X button
- Colored background (blue) for visibility

**4. Quick Action Buttons** (on agent cards)
- 📝 View Logs
- 🚨 View Alerts
- 📡 View Events
- 📊 View Metrics

### Backend API Updates

**Query Parameter: `agent`**

All observability endpoints support optional `agent` filter:

```
GET /api/platform/logs?agent=WowMemory&level=ERROR
GET /api/platform/alerts?agent=WowMemory&severity=critical
GET /api/platform/events?agent=WowMemory&event_type=error
GET /api/platform/metrics?agent=WowMemory
```

**Response Includes Context:**
```json
{
  "total": 15,
  "logs": [...],
  "filtered_by_agent": "WowMemory"
}
```

### Page Updates

**All pages get:**
1. Context selector in header
2. Subscribe to context changes via `AppContext.subscribe()`
3. Reload data when context changes
4. Add `agent` parameter to API calls if context set
5. Show context banner when filtered

---

## Acceptance Criteria

### Functional Requirements
- [ ] Context selector dropdown in header of all pages
- [ ] Selecting agent filters logs/alerts/events/metrics to that agent only
- [ ] "Platform-Wide" option shows aggregate data from all agents
- [ ] Context persists in localStorage (survives page refresh)
- [ ] Visual indicator shows current context in header
- [ ] Context banner shown on filtered pages with "View All" button
- [ ] Clicking agent card sets context (optional navigation)
- [ ] Quick action buttons on agent cards (4 buttons each)
- [ ] Auto-switch context when performing agent actions (deploy, start)
- [ ] Auto-switch context when clicking error notifications
- [ ] "Clear Filter" button resets to platform-wide view
- [ ] Context selector populated dynamically from agent registry

### Backend Requirements
- [ ] All observability APIs support `agent` query parameter
- [ ] Logs API filters by agent name/ID
- [ ] Alerts API filters by agent reference in title/message
- [ ] Events API filters by source_agent field
- [ ] Metrics API filters by agent-specific metrics
- [ ] API responses include `filtered_by_agent` field

### Edge Cases
- [ ] Context set to deleted/revoked agent → Auto-clear + warning
- [ ] Multiple browser tabs → Context syncs via localStorage events
- [ ] Deep linking: `/logs.html?agent=WowMemory` sets context on load
- [ ] No data for selected agent → "No logs for WowMemory" message
- [ ] Agent name case-insensitive matching
- [ ] URL parameters override localStorage on page load

### Performance
- [ ] Context switch < 100ms (localStorage write + reload)
- [ ] API response time unaffected by agent filter
- [ ] No memory leaks from context subscriptions
- [ ] localStorage cleanup on context clear

---

## UI/UX Design

### Context Selector (Header)
```
┌─────────────────────────────────────────────┐
│ WAOOAW    Context: [Platform-Wide ▼]   Nav │
└─────────────────────────────────────────────┘
```

### Context Indicator (when filtered)
```
┌─────────────────────────────────────────────┐
│ 🔵 Viewing: WowMemory          [Clear ✕]   │
└─────────────────────────────────────────────┘
```

### Agent Card Quick Actions
```
┌──────────────────────────┐
│ WowMemory               │
│ Tier 4 • v0.4.2         │
│ Status: RUNNING         │
├──────────────────────────┤
│ [📝] [🚨] [📡] [📊]    │
└──────────────────────────┘
```

### Context Banner on Logs Page
```
┌─────────────────────────────────────────────┐
│ 📋 Showing logs for: WowMemory [View All]  │
├─────────────────────────────────────────────┤
│ [Log entries...]                            │
└─────────────────────────────────────────────┘
```

---

## Technical Tasks

### Phase 1: Frontend Core (2 days)
1. Create `AppContext` state manager class
2. Add localStorage persistence
3. Implement pub/sub for context changes
4. Add context selector UI to header template
5. Add context indicator banner component
6. Write unit tests for context manager

### Phase 2: Page Integration (2 days)
7. Update logs.html to use context
8. Update alerts.html to use context
9. Update events.html to use context
10. Update metrics.html to use context
11. Add context subscription to each page
12. Add context banner to each page

### Phase 3: Agent Cards (1 day)
13. Add quick action buttons to agent cards
14. Wire up context switching on card click
15. Implement navigation + context switch functions
16. Add hover states and tooltips

### Phase 4: Backend (1 day)
17. Update logs API to support `agent` filter
18. Update alerts API to support `agent` filter
19. Update events API to support `agent` filter
20. Update metrics API to support `agent` filter
21. Add `filtered_by_agent` to API responses

### Phase 5: Testing & Polish (1 day)
22. Test cross-page navigation with context
23. Test localStorage persistence and sync
24. Test deep linking with URL parameters
25. Test edge cases (deleted agents, empty data)
26. Add E2E tests for context flows
27. Performance testing and optimization

**Total Estimate**: 7 days (1 developer)

---

## Testing Strategy

### Unit Tests
- AppContext state transitions
- localStorage read/write
- Context change notifications
- Edge case handling (invalid agents)

### Integration Tests
- API filtering by agent parameter
- Context persistence across page loads
- Multi-tab synchronization via localStorage events

### E2E Tests
- User selects WowMemory → Navigates to logs → Sees filtered logs
- User clicks quick action → Context switches + page navigates
- User deploys agent → Context auto-switches + logs shown
- User clears context → All pages show platform-wide data

### Manual Testing Scenarios
1. Select agent, refresh page → Context persists
2. Open two tabs, change context in one → Both tabs sync
3. Deploy agent → Context switches automatically
4. Error occurs → Click notification → Context switches
5. Deep link `/logs.html?agent=WowMemory` → Works on first load

---

## Success Metrics

### User Experience
- Time to find agent-specific logs: 30s → 5s (83% reduction)
- Context switches per troubleshooting session: Tracked
- User satisfaction: Survey after 2 weeks

### Technical
- API response time with `agent` filter < 100ms
- Context switch latency < 100ms
- localStorage sync latency < 50ms
- Zero context-related bugs in production

### Adoption
- 80% of portal sessions use context filtering within 1 week
- 50% of error investigations start with context switch
- Reduced support tickets for "can't find my agent's logs"

---

## Dependencies

### Prerequisites
- Existing logs/alerts/events/metrics pages ✅
- Agent registry with 14 agents ✅
- APIs returning observable data ✅

### Integrations
- EventBus for agent events (Story 5.1.5 - optional)
- Error notifications (Story 5.1.6 - optional)

### Infrastructure
- No new infrastructure required
- Uses existing frontend + backend

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| localStorage not available | Medium | Low | Fallback to sessionStorage, then memory-only |
| Context out of sync across tabs | Low | Medium | Use storage events to sync, accept slight delay |
| Deep linking breaks context | Low | Low | URL params override localStorage |
| Performance with many agents | Low | Low | Dropdown virtualization if >50 agents |

---

## Out of Scope

- ❌ Multi-agent context (selecting multiple agents)
- ❌ Custom context groups ("My Favorite Agents")
- ❌ Context history (recently viewed agents)
- ❌ Saved context presets
- ❌ Context-based permissions/RBAC

These may be added in future iterations.

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code reviewed and merged
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Performance benchmarks met
- [ ] Documentation updated (README, API docs)
- [ ] Deployed to staging and tested
- [ ] Product owner approval
- [ ] Deployed to production
- [ ] Monitoring dashboards updated

---

**This story enables efficient, focused troubleshooting by filtering the entire portal to a single agent's context.** 🎯

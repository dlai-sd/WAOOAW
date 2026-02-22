#!/bin/bash
# Create all 53 mobile stories as GitHub issues

set -e

cd /workspaces/WAOOAW

echo "📋 Creating GitHub issues for all 53 mobile stories..."
echo ""

# EPIC-1: Foundation & Setup (12 stories) - 3 already created

# Story 1.4
gh issue create \
  --title "Story 1.4: API Client Configuration" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.1

**Objective**: Create Axios API client with JWT interceptors

**Acceptance Criteria**:
- [ ] src/mobile/src/services/api/client.ts created
- [ ] Base URL configured (CP Backend API)
- [ ] JWT token interceptors implemented
- [ ] Error handling configured

**Copilot Prompt**: Create Axios API client for mobile app. Base URL from CP Backend. Include JWT interceptors." \
  --label "mobile,priority-p0"

# Story 1.5
gh issue create \
  --title "Story 1.5: Secure Storage Setup" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.1

**Objective**: Configure expo-secure-store for JWT storage

**Acceptance Criteria**:
- [ ] src/mobile/src/services/storage/secureStorage.ts created
- [ ] JWT tokens stored securely
- [ ] Platform-specific encryption (Keychain/Keystore)

**Copilot Prompt**: Create secure storage wrapper using expo-secure-store for JWT tokens." \
  --label "mobile"

# Story 1.6
gh issue create \
  --title "Story 1.6: Google OAuth2 Integration" \
  --body "**Epic**: EPIC-1 | **Priority**: P0 | **Dependencies**: Story 1.4, 1.5

**Objective**: Implement Google OAuth2 sign-in

**Acceptance Criteria**:
- [ ] expo-auth-session configured
- [ ] Google OAuth2 flow working
- [ ] Tokens stored in secure storage

**Copilot Prompt**: Implement Google OAuth2 using expo-auth-session. Match CP web OAuth flow." \
  --label "mobile,priority-p0"

# Story 1.7
gh issue create \
  --title "Story 1.7: JWT Token Management" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.5, 1.6

**Objective**: JWT refresh, validation, logout

**Acceptance Criteria**:
- [ ] Token refresh logic implemented
- [ ] Auto-refresh before expiry
- [ ] Logout clears tokens

**Copilot Prompt**: Create JWT token management service with auto-refresh." \
  --label "mobile"

# Story 1.8
gh issue create \
  --title "Story 1.8: Auth Service Implementation" \
  --body "**Epic**: EPIC-1 | **Priority**: P0 | **Dependencies**: Story 1.6, 1.7

**Objective**: Complete authentication service

**Acceptance Criteria**:
- [ ] src/mobile/src/services/auth/authService.ts complete
- [ ] Sign in, sign up, logout methods
- [ ] Zustand auth store

**Copilot Prompt**: Create auth service with Zustand store. Sign in/up/logout methods." \
  --label "mobile,priority-p0"

# Story 1.9
gh issue create \
  --title "Story 1.9: Sign In Screen" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.3, 1.8

**Objective**: Build sign-in UI

**Acceptance Criteria**:
- [ ] Sign in screen with Google button
- [ ] Loading states, error handling
- [ ] Matches CP web design

**Copilot Prompt**: Create sign-in screen using theme tokens. Google OAuth button." \
  --label "mobile"

# Story 1.10
gh issue create \
  --title "Story 1.10: Sign Up Screen" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.3, 1.8

**Objective**: Build sign-up UI

**Acceptance Criteria**:
- [ ] Sign up screen with form
- [ ] Validation, error messages
- [ ] Matches CP web design

**Copilot Prompt**: Create sign-up screen with form validation. Match CP web design." \
  --label "mobile"

# Story 1.11
gh issue create \
  --title "Story 1.11: Navigation Infrastructure" \
  --body "**Epic**: EPIC-1 | **Priority**: P0 | **Dependencies**: Story 1.3

**Objective**: Set up React Navigation

**Acceptance Criteria**:
- [ ] React Navigation configured
- [ ] Auth stack vs Main stack
- [ ] Tab navigation for main app

**Copilot Prompt**: Set up React Navigation with auth stack and tab navigation." \
  --label "mobile,priority-p0"

# Story 1.12
gh issue create \
  --title "Story 1.12: Core Screen Skeleton" \
  --body "**Epic**: EPIC-1 | **Priority**: P1 | **Dependencies**: Story 1.11

**Objective**: Create 5 main screen skeletons

**Acceptance Criteria**:
- [ ] Home, Agents, My Trials, Profile screens created
- [ ] Tab navigation working
- [ ] Basic layouts

**Copilot Prompt**: Create 5 main screen skeletons with tab navigation." \
  --label "mobile"

echo "✅ EPIC-1 stories created (12 total)"
echo ""

# EPIC-2: Core Features (15 stories)

gh issue create \
  --title "Story 2.1: Agent Service Implementation" \
  --body "**Epic**: EPIC-2 | **Priority**: P0 | **Dependencies**: EPIC-1 complete

**Objective**: Create agent API service (100% reuse CP Backend APIs)

**Acceptance Criteria**:
- [ ] src/mobile/src/services/agents/agentService.ts
- [ ] Methods: getAgents, getAgentById, searchAgents, filterAgents
- [ ] React Query hooks

**Copilot Prompt**: Create agent service using CP Backend API. React Query hooks." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 2.2: Agent List Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.1

**Objective**: Build agent browsing screen

**Acceptance Criteria**:
- [ ] Agent list with pagination
- [ ] Pull-to-refresh
- [ ] Loading/error states

**Copilot Prompt**: Create agent list screen with FlatList. Pagination, pull-to-refresh." \
  --label "mobile"

gh issue create \
  --title "Story 2.3: Agent Card Component" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.1

**Objective**: Reusable agent card component

**Acceptance Criteria**:
- [ ] Avatar, name, specialty, rating
- [ ] Status indicator (🟢/🟡/🔴)
- [ ] Price, activity stats

**Copilot Prompt**: Create agent card component matching CP web design." \
  --label "mobile"

gh issue create \
  --title "Story 2.4: Agent Search & Filters" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.2

**Objective**: Search bar and filter UI

**Acceptance Criteria**:
- [ ] Search by name/specialty
- [ ] Filter by industry, rating, price
- [ ] Debounced search

**Copilot Prompt**: Create search and filter UI for agents. Debounced search." \
  --label "mobile"

gh issue create \
  --title "Story 2.5: Agent Detail Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P0 | **Dependencies**: Story 2.1

**Objective**: Full agent profile view

**Acceptance Criteria**:
- [ ] Agent bio, skills, portfolio
- [ ] Reviews/testimonials
- [ ] 'Hire' button

**Copilot Prompt**: Create agent detail screen with bio, skills, reviews. Hire button." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 2.6: Hire Wizard - Step 1" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.5

**Objective**: Agent selection confirmation

**Copilot Prompt**: Create hire wizard step 1 - agent selection confirmation." \
  --label "mobile"

gh issue create \
  --title "Story 2.7: Hire Wizard - Step 2" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.6

**Objective**: Trial details (duration, deliverables)

**Copilot Prompt**: Create hire wizard step 2 - trial details form." \
  --label "mobile"

gh issue create \
  --title "Story 2.8: Hire Wizard - Step 3" \
  --body "**Epic**: EPIC-2 | **Priority**: P0 | **Dependencies**: Story 2.7

**Objective**: Payment summary

**Copilot Prompt**: Create hire wizard step 3 - payment summary screen." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 2.9: Razorpay SDK Integration" \
  --body "**Epic**: EPIC-2 | **Priority**: P0 | **Dependencies**: Story 2.8

**Objective**: Integrate Razorpay mobile SDK

**Copilot Prompt**: Integrate react-native-razorpay for payments." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 2.10: Hire Confirmation Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.8

**Objective**: Success confirmation

**Copilot Prompt**: Create hire confirmation screen with trial details." \
  --label "mobile"

gh issue create \
  --title "Story 2.11: Trial Service Implementation" \
  --body "**Epic**: EPIC-2 | **Priority**: P0 | **Dependencies**: Story 2.10

**Objective**: Trial management API service

**Copilot Prompt**: Create trial service using CP Backend trial APIs." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 2.12: My Agents Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.11

**Objective**: List of hired agents

**Copilot Prompt**: Create My Agents screen showing active and past agents." \
  --label "mobile"

gh issue create \
  --title "Story 2.13: Trial Dashboard Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.11

**Objective**: Active trial details

**Copilot Prompt**: Create trial dashboard with days remaining, deliverables." \
  --label "mobile"

gh issue create \
  --title "Story 2.14: Deliverables Viewer" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: Story 2.11

**Objective**: View trial deliverables

**Copilot Prompt**: Create deliverables viewer (files, links, documents)." \
  --label "mobile"

gh issue create \
  --title "Story 2.15: Profile Screen" \
  --body "**Epic**: EPIC-2 | **Priority**: P1 | **Dependencies**: EPIC-1 complete

**Objective**: User profile and settings

**Copilot Prompt**: Create profile screen with user info, settings, logout." \
  --label "mobile"

echo "✅ EPIC-2 stories created (15 total)"
echo ""

# EPIC-3: Voice Control (8 stories)

gh issue create \
  --title "Story 3.1: Voice UI Button Component" \
  --body "**Epic**: EPIC-3 | **Priority**: P1 | **Dependencies**: Story 1.11

**Objective**: Floating voice button on all screens

**Copilot Prompt**: Create floating voice button component with animations." \
  --label "mobile"

gh issue create \
  --title "Story 3.2: Speech Recognition Service" \
  --body "**Epic**: EPIC-3 | **Priority**: P0 | **Dependencies**: Story 1.1

**Objective**: Integrate @react-native-voice/voice

**Copilot Prompt**: Create speech recognition service using @react-native-voice/voice." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 3.3: Voice Command Parser" \
  --body "**Epic**: EPIC-3 | **Priority**: P0 | **Dependencies**: Story 3.1, 3.2

**Objective**: Parse 10+ voice commands

**Copilot Prompt**: Create command parser for 10+ voice commands (navigate, search, hire, etc)." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 3.4: Voice Feedback (TTS)" \
  --body "**Epic**: EPIC-3 | **Priority**: P1 | **Dependencies**: Story 3.3

**Objective**: Text-to-speech responses using expo-speech

**Copilot Prompt**: Create TTS feedback service using expo-speech." \
  --label "mobile"

gh issue create \
  --title "Story 3.5: Navigation Commands" \
  --body "**Epic**: EPIC-3 | **Priority**: P1 | **Dependencies**: Story 3.3

**Objective**: Voice navigation ('go to agents', 'open profile')

**Copilot Prompt**: Implement navigation voice commands." \
  --label "mobile"

gh issue create \
  --title "Story 3.6: Search Commands" \
  --body "**Epic**: EPIC-3 | **Priority**: P1 | **Dependencies**: Story 3.3

**Objective**: Voice search ('find marketing agents')

**Copilot Prompt**: Implement search voice commands." \
  --label "mobile"

gh issue create \
  --title "Story 3.7: Action Commands" \
  --body "**Epic**: EPIC-3 | **Priority**: P1 | **Dependencies**: Story 3.3

**Objective**: Voice actions ('hire this agent')

**Copilot Prompt**: Implement action voice commands (hire, cancel, etc)." \
  --label "mobile"

gh issue create \
  --title "Story 3.8: Hindi Language Support" \
  --body "**Epic**: EPIC-3 | **Priority**: P2 (Low) | **Dependencies**: Story 3.3

**Objective**: Hindi voice commands

**Copilot Prompt**: Add Hindi language support for voice commands." \
  --label "mobile"

echo "✅ EPIC-3 stories created (8 total)"
echo ""

# EPIC-4: Polish & Optimization (10 stories)

gh issue create \
  --title "Story 4.1: Performance Profiling" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: EPIC-2, EPIC-3 complete

**Objective**: Profile performance issues

**Copilot Prompt**: Set up React Native performance monitoring." \
  --label "mobile"

gh issue create \
  --title "Story 4.2: List Optimization (Virtualization)" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: Story 4.1

**Objective**: Optimize FlatList for large datasets

**Copilot Prompt**: Optimize FlatList with getItemLayout, keyExtractor." \
  --label "mobile"

gh issue create \
  --title "Story 4.3: Image Optimization" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: Story 4.1

**Objective**: Lazy loading, caching, compression

**Copilot Prompt**: Implement image lazy loading and caching." \
  --label "mobile"

gh issue create \
  --title "Story 4.4: Bundle Size Optimization" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: Story 4.1

**Objective**: Reduce bundle size (<5MB)

**Copilot Prompt**: Analyze and reduce bundle size. Remove unused dependencies." \
  --label "mobile"

gh issue create \
  --title "Story 4.5: Startup Time Optimization" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: Story 4.1

**Objective**: Cold start <2 seconds

**Copilot Prompt**: Optimize app startup time. Lazy load screens." \
  --label "mobile"

gh issue create \
  --title "Story 4.6: Offline Mode Implementation" \
  --body "**Epic**: EPIC-4 | **Priority**: P2 | **Dependencies**: Story 2.1

**Objective**: Cache agents, work offline

**Copilot Prompt**: Implement offline mode with React Query persistence." \
  --label "mobile"

gh issue create \
  --title "Story 4.7: Unit Test Suite Completion" \
  --body "**Epic**: EPIC-4 | **Priority**: P0 | **Dependencies**: EPIC-2 complete

**Objective**: 80%+ test coverage (Docker-only)

**Acceptance Criteria**:
- [ ] ALL tests run via Docker: \`docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test\`
- [ ] NO virtual environments used
- [ ] Coverage >80%

**Copilot Prompt**: Write unit tests for all services and components. Docker execution only." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 4.8: Integration Test Suite" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: EPIC-2 complete

**Objective**: Integration tests for API flows (Docker-only)

**Copilot Prompt**: Write integration tests for API services via Docker." \
  --label "mobile"

gh issue create \
  --title "Story 4.9: E2E Test Suite (Detox)" \
  --body "**Epic**: EPIC-4 | **Priority**: P1 | **Dependencies**: EPIC-2, EPIC-3 complete

**Objective**: Detox E2E tests in Docker

**Acceptance Criteria**:
- [ ] Detox configured for iOS/Android
- [ ] Tests run in Docker containers
- [ ] Critical flows tested (sign in, hire agent)

**Copilot Prompt**: Set up Detox E2E tests running in Docker." \
  --label "mobile"

gh issue create \
  --title "Story 4.10: Accessibility (A11y) Audit" \
  --body "**Epic**: EPIC-4 | **Priority**: P2 | **Dependencies**: EPIC-2 complete

**Objective**: WCAG 2.1 AA compliance

**Copilot Prompt**: Add accessibility labels, screen reader support." \
  --label "mobile"

echo "✅ EPIC-4 stories created (10 total)"
echo ""

# EPIC-5: Deployment (8 stories)

gh issue create \
  --title "Story 5.1: App Store Assets" \
  --body "**Epic**: EPIC-5 | **Priority**: P1 | **Dependencies**: EPIC-4 complete

**Objective**: Screenshots, video, app icons

**Copilot Prompt**: Generate app store assets (screenshots, video)." \
  --label "mobile"

gh issue create \
  --title "Story 5.2: Privacy Policy & Terms" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: None

**Objective**: Legal documents for app stores

**Copilot Prompt**: Create privacy policy and terms of service." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 5.3: Beta Build (TestFlight)" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: EPIC-4 complete

**Objective**: iOS TestFlight beta

**Copilot Prompt**: Create EAS Build for iOS TestFlight beta." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 5.4: Beta Build (Play Store Internal)" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: EPIC-4 complete

**Objective**: Android internal testing track

**Copilot Prompt**: Create EAS Build for Play Store internal testing." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 5.5: Beta Testing & Bug Fixes" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: Story 5.3, 5.4

**Objective**: 10 beta testers, collect feedback

**Copilot Prompt**: Set up beta testing feedback collection." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 5.6: Analytics Integration (Firebase)" \
  --body "**Epic**: EPIC-5 | **Priority**: P1 | **Dependencies**: EPIC-2 complete

**Objective**: Track user events, screen views

**Copilot Prompt**: Integrate Firebase Analytics for mobile." \
  --label "mobile"

gh issue create \
  --title "Story 5.7: Error Tracking (Sentry)" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: EPIC-2 complete

**Objective**: Crash reporting and monitoring

**Copilot Prompt**: Integrate Sentry for error tracking." \
  --label "mobile,priority-p0"

gh issue create \
  --title "Story 5.8: Production Release" \
  --body "**Epic**: EPIC-5 | **Priority**: P0 | **Dependencies**: Story 5.5

**Objective**: Submit to App Store and Play Store

**Copilot Prompt**: Create production builds for app store submission." \
  --label "mobile,priority-p0"

echo "✅ EPIC-5 stories created (8 total)"
echo ""
echo "✅✅✅ All 53 mobile stories created as GitHub issues! ✅✅✅"
echo ""
echo "View them: gh issue list --label mobile"
echo "Start Story 1.1: gh issue view 682"

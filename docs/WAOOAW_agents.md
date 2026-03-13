# WAOOAW Agents Session Handoff

Date: 2026-03-12
Repo: WAOOAW
Current branch at handoff: feat/plant-dma-1-it3-s4-regression-release

## CP Auth Outcome

- CP sign-in and sign-up were redesigned with a startup-style split layout and clearer OTP flow hierarchy.
- The redesign was isolated into a clean PR and opened as PR #925: feat(cp-auth): redesign startup sign-in and sign-up.
- Validation completed on the clean auth branch with:
  - focused CP auth/frontend tests: 32 passed
  - CP frontend build: passed

## Landing Page Outcome

- A separate experimental landing-page worktree and branch were created for exploration.
- The user rejected the landing-page redesign direction.
- Final decision: do not carry the landing experiment forward; keep the existing demo landing page.

## Digital Marketing Agent Direction For Next Session

- Next focus is the Digital Marketing Agent setup flow, starting in PP.
- PP should define the agent and configure skills cleanly so CP feels natural for the customer.
- The likely initial DMA skill grouping is:
  - Theme Discovery
  - Video Creator
  - YouTube Publisher

## YouTube Integration Findings

- WAOOAW should not assume the CP login identity and the YouTube identity are the same.
- Correct model: the customer may sign into CP with a business email, then connect a different Google account for YouTube channel access.
- CP identity proves who the customer is in WAOOAW.
- YouTube OAuth identity proves which external channel the hired agent may act on.

## Recommended Customer Flow

1. Customer hires the Digital Marketing Agent.
2. Customer opens the CP agent configuration wizard.
3. Customer selects the YouTube creation/publishing capability.
4. CP prompts the customer to connect YouTube via OAuth.
5. After OAuth, CP fetches channel metadata and asks the customer to confirm the channel identity.
6. Customer completes Theme Discovery, cadence, and content settings.
7. Agent creates drafts.
8. Customer reviews exact content.
9. Publish remains approval-gated and uses the connected YouTube credential.

## Important Technical Conclusions

- YouTube should use OAuth access_token and refresh_token, not a raw API-key setup flow.
- CP already has the right high-level pattern for platform connections:
  - store raw credentials in Secret Manager
  - persist only an opaque secret_ref for Plant runtime use
- Plant already contains YouTube-specific runtime code and credential resolution plumbing.
- Current gap: YouTube publishing is not fully wired into the real destination adapter path everywhere; some publisher-engine paths still treat youtube as simulated.

## Existing Relevant Files

- CP Secret Manager write path:
  - src/CP/BackEnd/api/cp_skills.py
  - src/CP/BackEnd/services/secret_manager.py
- CP internal credential resolution path:
  - src/CP/BackEnd/api/internal_plant_credential_resolver.py
  - src/CP/BackEnd/services/platform_credentials.py
- Plant credential resolution and YouTube integration:
  - src/Plant/BackEnd/services/social_credential_resolver.py
  - src/Plant/BackEnd/integrations/social/youtube_client.py
  - src/Plant/BackEnd/agent_mold/skills/publisher_engine.py

## Cross-Platform Connector View

- YouTube: strong fit for OAuth-based external account connection.
- Facebook and Instagram: similar OAuth/business-asset pattern, not customer app-secret harvesting.
- LinkedIn: OAuth-based identity and organization/page permission pattern.
- X: possible, but commercial/API stability is weaker than YouTube, Meta, and LinkedIn.
- WhatsApp: business onboarding flow is different and more operationally specific than a simple social connect flow.

## Product Rule To Preserve

- Never couple WAOOAW account login identity to external publishing identity.
- Always show the customer exactly which external channel/account/page/organization is connected before enabling publish.
- Approval-gated publishing and truthful runtime readiness must remain visible in both CP and PP.
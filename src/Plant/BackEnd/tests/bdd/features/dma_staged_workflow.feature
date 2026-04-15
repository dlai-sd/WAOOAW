Feature: DMA Staged Workflow — Theme to Content to Publish
  As a customer using the Digital Marketing Agent
  I want to review an AI-generated content theme before any content is produced
  So that I can ensure brand alignment before approving execution

  # ── Scenario 1: Full happy path ─────────────────────────────────────────────

  @bdd @dma
  Scenario: Customer approves theme batch and triggers content creation
    Given a customer "CUST-BDD-001" has hired DMA agent "AGT-MKT-DMA-001"
    When the customer submits a theme batch for "Care Clinic" on channel "youtube"
    Then the batch is created with status "pending_review"
    And all posts are in state "pending_review"
    When the customer approves all posts in the theme batch
    Then each post has review_status "approved"
    When the customer triggers content batch creation from the approved theme
    Then a new content batch is created linked to the theme batch
    And the content batch has batch_type "content"

  # ── Scenario 2: Approval gate blocks early content creation ─────────────────

  @bdd @dma
  Scenario: Content creation is blocked until all theme posts are approved
    Given a customer "CUST-BDD-002" has hired DMA agent "AGT-MKT-DMA-001"
    When the customer submits a theme batch for "Brand X" on channel "youtube"
    And the customer has NOT approved all posts
    When the customer attempts to create a content batch from the unapproved theme
    Then the request is rejected with status 403
    And the rejection reason is "theme_not_fully_approved"

  # ── Scenario 3: Secret adapter wiring ───────────────────────────────────────

  @bdd @dma
  Scenario: Local secret adapter rejects GCP-format credential refs
    Given the secret backend is configured as "local"
    When a GCP-format credential ref is read
    Then the adapter raises a ValueError containing "Unsupported local secret ref"

  @bdd @dma
  Scenario: GCP secret adapter is selected when SECRET_MANAGER_BACKEND is gcp
    Given the secret backend is configured as "gcp"
    And GCP_PROJECT_ID is set to "waooaw-oauth"
    Then the factory returns a GcpSecretManagerAdapter

  # ── Scenario 4: Rejected posts are never published ───────────────────────────

  @bdd @dma
  Scenario: Rejected content post cannot be published
    Given a customer "CUST-BDD-003" has a content post
    When the customer rejects the post with reason "wrong tone"
    And the customer attempts to publish the rejected post
    Then the publish request is rejected with status 403

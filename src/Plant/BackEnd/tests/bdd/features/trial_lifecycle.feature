Feature: 7-Day Trial Lifecycle
  As a customer
  I want to start a 7-day trial of an AI agent
  So that I can evaluate the agent before committing to a subscription

  @bdd
  Scenario: Start a new trial
    Given a customer with email "test@example.com"
    And an agent with id "agent-001"
    When the customer starts a trial for the agent
    Then the trial status is "active"
    And the trial duration is 7 days

  @bdd
  Scenario: Trial is cancelled and customer keeps deliverables
    Given an active trial with one deliverable
    When the customer cancels the trial
    Then the trial status is "cancelled"
    And the deliverable is still accessible

  @bdd
  Scenario: Trial auto-expires after 7 days
    Given an active trial started 8 days ago
    When the expiry check runs
    Then the trial status is "expired"

  @bdd
  Scenario: Usage cap is enforced during trial
    Given an active trial with a token limit of 1000
    When 1000 tokens have been used
    Then further usage is rejected with "cap exceeded"

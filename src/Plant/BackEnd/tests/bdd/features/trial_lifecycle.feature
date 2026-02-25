Feature: 7-day Trial Lifecycle
  As a customer platform user
  I want to start and manage a 7-day agent trial
  So that I can evaluate agents before hiring

  Background:
    Given the WAOOAW platform is running

  Scenario: Customer starts a trial
    Given a customer "test@example.com" exists
    And an agent "agent-001" is available
    When the customer starts a trial for agent "agent-001"
    Then a trial is created with status "active"
    And the trial expires in 7 days

  Scenario: Trial usage cap is enforced
    Given an active trial exists
    When the customer uses 100% of the trial allocation
    Then further usage is blocked

  Scenario: Customer cancels trial and keeps deliverables
    Given an active trial with deliverables exists
    When the customer cancels the trial
    Then the trial status becomes "cancelled"
    And the deliverables remain accessible

  Scenario: Trial auto-expires after 7 days
    Given a trial that started 8 days ago
    When the expiry check runs
    Then the trial status becomes "expired"

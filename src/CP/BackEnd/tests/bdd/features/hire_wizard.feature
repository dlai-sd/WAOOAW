Feature: Hire Wizard Flow
  As a customer
  I want to hire an AI agent through a step-by-step wizard
  So that I can configure my subscription before payment

  @bdd
  Scenario: Draft a new hire
    Given a customer with id "cp-user-001"
    And an agent type "marketing-agent"
    When the customer starts the hire wizard
    Then a draft hire is created with status "draft"

  @bdd
  Scenario: Advance wizard step
    Given a draft hire at step 1
    When the customer advances to step 2
    Then the hire is at step 2

  @bdd
  Scenario: Apply coupon during hire
    Given a draft hire with base price 10000
    When the customer applies coupon "SAVE20"
    Then the discounted price is 8000

  @bdd
  Scenario: Complete payment and confirm hire
    Given a draft hire ready for payment
    When payment is confirmed
    Then the hire status is "active"
    And a trial is started

  @bdd
  Scenario: Cancel hire wizard
    Given a draft hire
    When the customer cancels the wizard
    Then the hire status is "cancelled"

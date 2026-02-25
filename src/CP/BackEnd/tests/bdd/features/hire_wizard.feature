Feature: CP Hire Wizard Flow
  As a customer platform user
  I want to hire an agent through the wizard
  So that I can get AI assistance for my business

  Background:
    Given the CP backend is running

  Scenario: Customer creates a draft hire
    Given a logged-in customer
    When they start a hire wizard for agent "agent-001"
    Then a hire draft is created
    And the wizard is at step 1

  Scenario: Customer advances wizard steps
    Given a hire draft at step 1
    When the customer completes step 1
    Then the wizard advances to step 2

  Scenario: Customer applies a coupon
    Given a hire draft at payment step
    When the customer applies coupon "TRIAL10"
    Then the discount is applied to the total

  Scenario: Customer completes payment
    Given a hire draft with coupon applied
    When the customer confirms payment
    Then the hire is confirmed
    And a trial period begins

  Scenario: Customer cancels hire wizard
    Given a hire draft in progress
    When the customer cancels
    Then the draft is deleted

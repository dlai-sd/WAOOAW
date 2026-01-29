---
playbook_id: MARKETING.MULTICHANNEL.POST.V1
name: Multi-channel themed post
version: 1.0.0
category: marketing
description: Create a canonical marketing message and adapt it to LinkedIn + Instagram.
output_contract: marketing_multichannel_v1
required_inputs:
  - theme
  - brand_name
steps:
  - Draft canonical message (theme + brand + offer + location)
  - Adapt to LinkedIn (bullets + CTA)
  - Adapt to Instagram (caption + hashtags)
quality_checks:
  - No false claims
  - CTA is clear
  - Output respects channel length limits
  - Hashtags are normalized
---

# Skill: Multi-channel themed post

This playbook is intentionally minimal for Chunk C.

In later chunks, steps may be executed using AI Explorer prompt templates,
with strict output schema validation.

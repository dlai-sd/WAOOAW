#!/usr/bin/env python3
"""
Test Agent Identity Framework

Tests dual-identity system:
- Specialization (CoE template)
- Personality (instance identity)
- introduce_self() functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'waooaw'))

from agents.wowvision_prime import WowVisionPrime
from config.loader import load_config

def test_specialization():
    """Test 1: Agent has clear specialization"""
    print("\n" + "="*60)
    print("TEST 1: Specialization Identity")
    print("="*60)
    
    config = load_config()
    agent = WowVisionPrime(config)
    
    # Check specialization
    print(f"\n✅ CoE Name: {agent.specialization.coe_name}")
    print(f"✅ Domain: {agent.specialization.domain}")
    print(f"✅ Expertise: {agent.specialization.expertise}")
    
    print(f"\n📋 Responsibilities:")
    for resp in agent.specialization.core_responsibilities:
        print(f"  - {resp}")
    
    print(f"\n⚠️  Constraints:")
    for constraint in agent.specialization.constraints:
        print(f"  - {constraint['rule']}")
        print(f"    Reason: {constraint['reason']}")
    
    # Test capability check
    can_create_issue = agent.specialization.can_do("GitHub issue creation and management")
    can_modify_layer1 = agent.specialization.is_constrained("modify vision stack Layer 1")
    
    print(f"\n🔍 Capability Tests:")
    print(f"  Can create GitHub issues: {can_create_issue}")
    print(f"  Can modify Layer 1: {'No' if can_modify_layer1 else 'Yes'} {f'({can_modify_layer1})' if can_modify_layer1 else ''}")
    
    assert agent.specialization.coe_name == "WowVision Prime"
    assert len(agent.specialization.core_responsibilities) > 0
    assert len(agent.specialization.constraints) > 0
    
    print("\n✅ TEST 1 PASSED: Specialization loaded correctly")
    return agent


def test_personality(agent):
    """Test 2: Agent has personality (default or custom)"""
    print("\n" + "="*60)
    print("TEST 2: Personality Identity")
    print("="*60)
    
    print(f"\n👤 Instance ID: {agent.personality.instance_id}")
    print(f"👤 Instance Name: {agent.personality.instance_name or '(Not hired yet - marketplace mode)'}")
    print(f"👤 Role Title: {agent.personality.role_title or '(Not set)'}")
    print(f"👤 Industry: {agent.personality.industry or '(Not set)'}")
    print(f"👤 Status: {agent.personality.status}")
    
    if agent.personality.instance_name:
        print(f"\n🏢 Employer: {agent.personality.employer.get('company_name', 'Unknown')}")
        print(f"🎯 Focus Areas: {', '.join(agent.personality.focus_areas) if agent.personality.focus_areas else 'General'}")
    
    assert agent.personality.instance_id is not None
    assert agent.personality.status == "active"
    
    print("\n✅ TEST 2 PASSED: Personality loaded correctly")


def test_introduction(agent):
    """Test 3: Agent can introduce itself"""
    print("\n" + "="*60)
    print("TEST 3: Self-Introduction")
    print("="*60)
    
    intro = agent.introduce_self()
    
    print(f"\n🗣️  Agent says:")
    print(f"   \"{intro}\"")
    
    # Verify introduction contains key elements
    assert "WowVision Prime" in intro
    assert "vision" in intro.lower() or "Vision" in intro
    
    print("\n✅ TEST 3 PASSED: Agent can introduce itself")
    
    return intro


if __name__ == "__main__":
    print("\n🧪 TESTING DUAL-IDENTITY FRAMEWORK")
    print("="*60)
    
    try:
        agent = test_specialization()
        test_personality(agent)
        test_introduction(agent)
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nThe agent now has:")
        print("  ✅ Specialization (what type of agent)")
        print("  ✅ Personality (who specifically)")
        print("  ✅ Self-awareness (can introduce itself)")
        print("\nNext: Implement output generation (GitHub issues, comments, reports)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

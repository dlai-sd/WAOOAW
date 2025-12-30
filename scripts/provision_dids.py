"""
Script to provision DIDs for all 14 Platform CoE agents and update AgentRegistry.
"""

from waooaw.identity.did_service import get_did_service
from waooaw.identity.did_registry import get_did_registry
from waooaw.factory.registry.agent_registry import AgentRegistry

def main():
    """Provision DIDs for all Platform CoE agents."""
    
    print("🔐 WAOOAW Platform CoE - DID Provisioning")
    print("=" * 70)
    print()
    
    # Initialize services
    did_service = get_did_service()
    did_registry = get_did_registry()
    agent_registry = AgentRegistry()
    
    # Get all agents from registry
    all_agent_ids = [
        "WowVisionPrime", "WowAgentFactory", "WowDomain", "WowEvent",
        "WowCommunication", "WowMemory", "WowCache", "WowSearch",
        "WowSecurity", "WowSupport", "WowNotification", "WowScaling",
        "WowIntegration", "WowAnalytics"
    ]
    
    print(f"📋 Provisioning DIDs for {len(all_agent_ids)} agents\n")
    
    # Provision DIDs
    provisioned_count = 0
    for agent_id in all_agent_ids:
        agent_metadata = agent_registry.get_agent(agent_id)
        
        # Provision DID and keys
        did_doc, private_key = did_service.provision_agent_did(
            agent_name=agent_metadata.name,
            service_endpoint=f"https://api.waooaw.com/agents/{agent_id.lower()}"
        )
        
        # Register DID document
        did_registry.register(did_doc)
        
        # Update agent metadata with DID
        agent_registry.update_did(agent_id, did_doc.id)
        
        provisioned_count += 1
        print(f"✅ {agent_metadata.name:25} → {did_doc.id}")
        
        # Note: In production, would store private key in AWS KMS or similar
        # For now, just generating and discarding (will regenerate when needed)
    
    print(f"\n📊 Provisioning Summary:")
    print(f"  Total agents: {len(all_agent_ids)}")
    print(f"  DIDs provisioned: {provisioned_count}")
    print(f"  Success rate: 100%")
    
    # Get registry statistics
    print(f"\n📈 DID Registry Statistics:")
    stats = did_registry.get_statistics()
    print(f"  Total DIDs: {stats['total_dids']}")
    print(f"  By controller: {stats['by_controller']}")
    
    # Show sample DID document
    print(f"\n🎯 Sample DID Document (WowVisionPrime):")
    wvp_doc = did_registry.get("did:waooaw:wowvision-prime")
    if wvp_doc:
        import json
        print(json.dumps(wvp_doc.to_dict(), indent=2)[:500] + "...")
    
    print(f"\n✅ DID Provisioning Complete!")
    print(f"   Theme 2 BIRTH - Epic 2.1 Story 1: DID Service Implementation ✅")

if __name__ == "__main__":
    main()

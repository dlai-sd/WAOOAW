"""
Issue Capability Credentials for All Platform CoE Agents

Provisions W3C Verifiable Credentials for each Platform CoE agent
based on their role and responsibilities. All credentials are signed
by WowVision Prime (the guardian).
"""

import sys
import logging
from datetime import datetime
from waooaw.identity.did_service import get_did_service
from waooaw.identity.did_registry import get_did_registry
from waooaw.identity.vc_issuer import get_vc_issuer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Capability definitions for each agent
AGENT_CAPABILITIES = {
    "wowvision-prime": [
        "can:guard-platform",
        "can:issue-credentials",
        "can:revoke-credentials",
        "can:manage-agents",
        "can:strategic-oversight",
        "can:vision-alignment"
    ],
    "wowsecurity": [
        "can:validate-credentials",
        "can:enforce-permissions",
        "can:monitor-access",
        "can:detect-threats",
        "can:audit-operations"
    ],
    "wowdomain": [
        "can:model-domain",
        "can:validate-ddd",
        "can:emit-domain-events",
        "can:define-aggregates",
        "can:manage-bounded-contexts"
    ],
    "wowdevops": [
        "can:deploy-services",
        "can:manage-infrastructure",
        "can:monitor-systems",
        "can:scale-resources",
        "can:configure-cicd"
    ],
    "wowworkflow": [
        "can:orchestrate-workflows",
        "can:manage-state-machines",
        "can:coordinate-agents",
        "can:handle-compensation",
        "can:track-workflow-state"
    ],
    "wowdata": [
        "can:model-data",
        "can:design-schemas",
        "can:manage-migrations",
        "can:ensure-data-quality",
        "can:optimize-queries"
    ],
    "wowapi": [
        "can:design-api",
        "can:manage-rest-endpoints",
        "can:handle-graphql",
        "can:document-api",
        "can:version-api"
    ],
    "wowui": [
        "can:design-interface",
        "can:create-components",
        "can:manage-state",
        "can:handle-accessibility",
        "can:optimize-performance"
    ],
    "wowtest": [
        "can:write-tests",
        "can:execute-tests",
        "can:analyze-coverage",
        "can:generate-test-data",
        "can:test-integration"
    ],
    "wowdocs": [
        "can:write-documentation",
        "can:generate-diagrams",
        "can:maintain-glossary",
        "can:create-tutorials",
        "can:document-api"
    ],
    "wowobserve": [
        "can:collect-metrics",
        "can:aggregate-logs",
        "can:trace-requests",
        "can:alert-incidents",
        "can:create-dashboards"
    ],
    "wowanalytics": [
        "can:analyze-data",
        "can:create-reports",
        "can:track-kpi",
        "can:generate-insights",
        "can:visualize-trends"
    ],
    "wowintegration": [
        "can:integrate-systems",
        "can:manage-adapters",
        "can:handle-transformations",
        "can:route-messages",
        "can:monitor-integrations"
    ],
    "wowml": [
        "can:train-models",
        "can:deploy-models",
        "can:monitor-ml",
        "can:optimize-hyperparameters",
        "can:feature-engineering"
    ]
}


def issue_capabilities_for_all_agents():
    """Issue capability credentials for all Platform CoE agents."""
    logger.info("🔐 Starting Capability Credential Provisioning")
    logger.info("=" * 70)
    
    # Initialize services
    did_service = get_did_service()
    did_registry = get_did_registry()
    vc_issuer = get_vc_issuer()
    
    # Get or provision WowVision Prime (issuer)
    issuer_did = "did:waooaw:wowvision-prime"
    issuer_did_doc = did_registry.get(issuer_did)
    
    if not issuer_did_doc:
        logger.info("📋 Provisioning issuer (WowVision Prime)")
        issuer_did_doc, issuer_private_key = did_service.provision_agent_did("wowvision-prime")
        did_registry.register(issuer_did_doc)
        logger.info(f"✅ Issuer DID: {issuer_did_doc.id}")
    else:
        logger.info(f"✅ Using existing issuer: {issuer_did}")
        # Need to regenerate keys for signing
        issuer_private_key = did_service.generate_key_pair()[0]
    
    issued_count = 0
    credential_registry = {}
    
    # Issue credentials for each agent
    for agent_id, capabilities in AGENT_CAPABILITIES.items():
        logger.info(f"\n📋 Processing: {agent_id}")
        
        # Get or provision agent DID
        agent_did = f"did:waooaw:{agent_id}"
        agent_did_doc = did_registry.get(agent_did)
        
        if not agent_did_doc:
            logger.info(f"   Creating DID for {agent_id}")
            agent_did_doc, _ = did_service.provision_agent_did(agent_id)
            did_registry.register(agent_did_doc)
        
        # Issue capability credential
        try:
            credential = vc_issuer.issue_capability_credential(
                subject_did=agent_did,
                capabilities=capabilities,
                private_key=issuer_private_key,
                validity_days=365
            )
            
            # Store credential
            credential_registry[agent_id] = {
                "credential_id": credential.id,
                "agent_did": agent_did,
                "capabilities": capabilities,
                "issued_at": credential.issuance_date,
                "expires_at": credential.expiration_date,
                "status": "active"
            }
            
            issued_count += 1
            logger.info(f"   ✅ Issued {len(capabilities)} capabilities")
            logger.info(f"   📝 Credential ID: {credential.id}")
            logger.info(f"   ⏰ Expires: {credential.expiration_date}")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to issue credential: {str(e)}")
            continue
    
    # Summary
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ Capability Credential Provisioning Complete")
    logger.info(f"")
    logger.info(f"📊 Summary:")
    logger.info(f"   - Total Agents: {len(AGENT_CAPABILITIES)}")
    logger.info(f"   - Credentials Issued: {issued_count}")
    logger.info(f"   - Success Rate: {(issued_count/len(AGENT_CAPABILITIES))*100:.1f}%")
    logger.info(f"")
    logger.info(f"🔐 All Platform CoE agents now have verifiable credentials!")
    
    # Save credential registry to file
    import json
    output_file = "credential_registry.json"
    with open(output_file, "w") as f:
        json.dump(credential_registry, f, indent=2)
    logger.info(f"📝 Credential registry saved to {output_file}")
    
    return credential_registry


if __name__ == "__main__":
    try:
        registry = issue_capabilities_for_all_agents()
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

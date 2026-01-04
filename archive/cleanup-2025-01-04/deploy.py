#!/usr/bin/env python3
"""
WAOOAW Infrastructure Deployment Script
Deploys complete infrastructure using GCP Deployment Manager

Single IP (35.190.6.91) routes to ALL environments:
- Demo: cp.demo.waooaw.com, pp.demo.waooaw.com
- UAT: cp.uat.waooaw.com, pp.uat.waooaw.com  
- Prod: www.waooaw.com, pp.waooaw.com

Usage:
  ./deploy.py --environment demo --action create
  ./deploy.py --environment uat --action update --preview
  ./deploy.py --environment prod --action delete
"""

import argparse
import subprocess
import sys
import yaml
import os
from pathlib import Path

# Configuration
ENVIRONMENTS = ["demo", "uat", "prod"]
ACTIONS = ["create", "update", "delete", "preview"]
PROJECT = "waooaw-oauth"
DOMAIN = "waooaw.com"

# Single static IP for ALL environments (cost savings!)
STATIC_IP_NAME = "waooaw-lb-ip"
STATIC_IP_ADDRESS = "35.190.6.91"  # Existing IP - reuse it!

# Domain configuration per environment
DOMAINS = {
    "demo": {
        "customer_portal": f"cp.demo.{DOMAIN}",
        "platform_portal": f"pp.demo.{DOMAIN}"
    },
    "uat": {
        "customer_portal": f"cp.uat.{DOMAIN}",
        "platform_portal": f"pp.uat.{DOMAIN}"
    },
    "prod": {
        "customer_portal": f"www.{DOMAIN}",  # Production uses www, not cp
        "platform_portal": f"pp.{DOMAIN}"
    }
}

# Region configuration
REGIONS = {
    "demo": ["asia-south1"],
    "uat": ["asia-south1"],
    "prod": ["asia-south1", "us-central1"]  # Multi-region for prod
}

# Scaling configuration
SCALING = {
    "demo": {
        "minInstances": 0,
        "maxInstances": 5,
        "concurrency": 80,
        "cpuThrottling": True
    },
    "uat": {
        "minInstances": 1,
        "maxInstances": 10,
        "concurrency": 80,
        "cpuThrottling": False
    },
    "prod": {
        "minInstances": 2,
        "maxInstances": 100,
        "concurrency": 80,
        "cpuThrottling": False
    }
}

def generate_config(environment, version="latest"):
    """Generate deployment configuration"""
    
    primary_region = REGIONS[environment][0]
    scaling = SCALING[environment]
    domains = DOMAINS[environment]
    
    config = {
        "imports": [
            {"path": "templates/cloud-run.jinja"},
            {"path": "templates/load-balancer.jinja"},
            {"path": "templates/networking.jinja"}
        ],
        "resources": [
            # Networking - Single Static IP (shared across all environments)
            {
                "name": f"{environment}-networking",
                "type": "templates/networking.jinja",
                "properties": {
                    "environment": environment,
                    "staticIpName": STATIC_IP_NAME,
                    "staticIpAddress": STATIC_IP_ADDRESS,  # Reuse existing IP
                    "createStaticIp": False,  # Don't create, use existing
                    "vpcConnector": {
                        "enabled": False  # Enable when Cloud SQL is added
                    }
                }
            },
            # Backend Service (API for both portals)
            {
                "name": f"waooaw-api-{environment}",
                "type": "templates/cloud-run.jinja",
                "properties": {
                    "name": f"waooaw-api-{environment}",
                    "environment": environment,
                    "serviceType": "backend",
                    "region": primary_region,
                    "container": {
                        "image": f"asia-south1-docker.pkg.dev/{PROJECT}/waooaw/backend-v2:{version}",
                        "port": 8000
                    },
                    "resources": {
                        "cpu": "1",
                        "memory": "512Mi"
                    },
                    "scaling": {
                        "minInstances": scaling["minInstances"],
                        "maxInstances": scaling["maxInstances"],
                        "concurrency": scaling["concurrency"],
                        "cpuThrottling": scaling["cpuThrottling"]
                    },
                    "envVars": [
                        {"name": "ENV", "value": environment},
                        {"name": "LOG_LEVEL", "value": "info"},
                        {"name": "DB_SCHEMA", "value": "public"}
                    ],
                    "secrets": [
                        {"name": "GOOGLE_CLIENT_ID", "secretName": "GOOGLE_CLIENT_ID"},
                        {"name": "GOOGLE_CLIENT_SECRET", "secretName": "GOOGLE_CLIENT_SECRET"},
                        {"name": "JWT_SECRET", "secretName": "JWT_SECRET"}
                    ],
                    "serviceAccount": f"waooaw-backend-{environment}@{PROJECT}.iam.gserviceaccount.com",
                    "executionEnvironment": "gen2",
                    "timeout": 300
                }
            },
            # Customer Portal Service (Marketplace)
            {
                "name": f"waooaw-portal-{environment}",
                "type": "templates/cloud-run.jinja",
                "properties": {
                    "name": f"waooaw-portal-{environment}",
                    "environment": environment,
                    "serviceType": "customer-portal",
                    "region": primary_region,
                    "container": {
                        "image": f"asia-south1-docker.pkg.dev/{PROJECT}/waooaw/customer-portal-v2:{version}",
                        "port": 8080
                    },
                    "resources": {
                        "cpu": "1",
                        "memory": "512Mi"
                    },
                    "scaling": {
                        "minInstances": scaling["minInstances"],
                        "maxInstances": scaling["maxInstances"],
                        "concurrency": scaling["concurrency"],
                        "cpuThrottling": scaling["cpuThrottling"]
                    },
                    "envVars": [
                        {"name": "ENV", "value": environment},
                        {"name": "LOG_LEVEL", "value": "info"}
                    ],
                    "secrets": [],
                    "serviceAccount": f"waooaw-portal-{environment}@{PROJECT}.iam.gserviceaccount.com",
                    "executionEnvironment": "gen2",
                    "timeout": 300
                }
            },
            # Platform Portal Service (Internal Ops)
            {
                "name": f"waooaw-platform-portal-{environment}",
                "type": "templates/cloud-run.jinja",
                "properties": {
                    "name": f"waooaw-platform-portal-{environment}",
                    "environment": environment,
                    "serviceType": "platform-portal",
                    "region": primary_region,
                    "container": {
                        "image": f"asia-south1-docker.pkg.dev/{PROJECT}/waooaw/platform-portal-v2:{version}",
                        "port": 8080  # Reflex default
                    },
                    "resources": {
                        "cpu": "1",
                        "memory": "1Gi"  # Reflex needs more memory
                    },
                    "scaling": {
                        "minInstances": scaling["minInstances"],
                        "maxInstances": scaling["maxInstances"],
                        "concurrency": scaling["concurrency"],
                        "cpuThrottling": scaling["cpuThrottling"]
                    },
                    "envVars": [
                        {"name": "ENV", "value": environment},
                        {"name": "LOG_LEVEL", "value": "info"}
                    ],
                    "secrets": [],
                    "serviceAccount": f"waooaw-platform-{environment}@{PROJECT}.iam.gserviceaccount.com",
                    "executionEnvironment": "gen2",
                    "timeout": 300
                }
            },
            # Load Balancer (Multi-domain routing)
            {
                "name": f"{environment}-load-balancer",
                "type": "templates/load-balancer.jinja",
                "properties": {
                    "environment": environment,
                    "domains": domains,
                    "staticIpName": STATIC_IP_NAME,
                    "staticIpAddress": STATIC_IP_ADDRESS,
                    "backends": {
                        "api": [
                            {
                                "serviceName": f"waooaw-api-{environment}",
                                "maxRate": 80,
                                "capacityScaler": 1.0
                            }
                        ],
                        "customer": [
                            {
                                "serviceName": f"waooaw-portal-{environment}",
                                "maxRate": 80,
                                "capacityScaler": 1.0
                            }
                        ],
                        "platform": [
                            {
                                "serviceName": f"waooaw-platform-portal-{environment}",
                                "maxRate": 80,
                                "capacityScaler": 1.0
                            }
                        ]
                    },
                    "healthCheck": {
                        "interval": 10,
                        "timeout": 5,
                        "healthyThreshold": 2,
                        "unhealthyThreshold": 3
                    },
                    "logSampleRate": 1.0 if environment == "demo" else 0.1
                },
                "metadata": {
                    "dependsOn": [
                        f"{environment}-networking",
                        f"waooaw-api-{environment}",
                        f"waooaw-portal-{environment}",
                        f"waooaw-platform-portal-{environment}"
                    ]
                }
            }
        ]
    }
    
    return config

def deploy(environment, action, preview=False, version="latest"):
    """Deploy infrastructure"""
    
    domains = DOMAINS[environment]
    print(f"🚀 {action.upper()} Infrastructure for {environment.upper()} environment")
    print(f"   Project: {PROJECT}")
    print(f"   Domains: {domains['customer_portal']}, {domains['platform_portal']}")
    print(f"   Version: {version}")
    print(f"   Static IP: {STATIC_IP_ADDRESS}")
    print("=" * 80)
    
    # Copy templates to /tmp for Deployment Manager
    import shutil
    templates_src = Path(__file__).parent / "templates"
    templates_dst = Path("/tmp/templates")
    
    if templates_dst.exists():
        shutil.rmtree(templates_dst)
    shutil.copytree(templates_src, templates_dst)
    print(f"✅ Copied templates to {templates_dst}")
    
    # Generate config
    config = generate_config(environment, version)
    config_file = Path(f"/tmp/waooaw-{environment}-config.yaml")
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Generated config: {config_file}")
    
    # Build gcloud command
    deployment_name = f"waooaw-{environment}-infra"
    
    if action == "create":
        cmd = [
            "gcloud", "deployment-manager", "deployments", "create",
            deployment_name,
            "--config", str(config_file),
            "--project", PROJECT
        ]
    elif action == "update":
        cmd = [
            "gcloud", "deployment-manager", "deployments", "update",
            deployment_name,
            "--config", str(config_file),
            "--project", PROJECT
        ]
        if preview:
            cmd.append("--preview")
    elif action == "delete":
        cmd = [
            "gcloud", "deployment-manager", "deployments", "delete",
            deployment_name,
            "--project", PROJECT,
            "--quiet"
        ]
        # Confirm deletion
        confirm = input(f"⚠️  Are you sure you want to DELETE {environment} infrastructure? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Deletion cancelled")
            return
    
    # Execute
    print(f"\n📦 Executing: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(' '.join(cmd), shell=True, check=True, text=True)
        
        print("\n" + "=" * 80)
        print(f"✅ {action.upper()} completed successfully!")
        
        if action in ["create", "update"] and not preview:
            print_post_deployment_instructions(environment)
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

def print_post_deployment_instructions(environment):
    """Print DNS and OAuth configuration instructions"""
    
    domains = DOMAINS[environment]
    
    print("\n" + "=" * 80)
    print("📋 POST-DEPLOYMENT CONFIGURATION REQUIRED")
    print("=" * 80)
    
    print(f"\n1️⃣  DNS Configuration (GoDaddy) - ALL USE SAME IP!")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if environment == "demo":
        print(f"   Type: A, Host: cp.demo,  Points to: {STATIC_IP_ADDRESS}, TTL: 600")
        print(f"   Type: A, Host: pp.demo,  Points to: {STATIC_IP_ADDRESS}, TTL: 600")
    elif environment == "uat":
        print(f"   Type: A, Host: cp.uat,   Points to: {STATIC_IP_ADDRESS}, TTL: 600")
        print(f"   Type: A, Host: pp.uat,   Points to: {STATIC_IP_ADDRESS}, TTL: 600")
    elif environment == "prod":
        print(f"   Type: A, Host: www,      Points to: {STATIC_IP_ADDRESS}, TTL: 600")
        print(f"   Type: A, Host: pp,       Points to: {STATIC_IP_ADDRESS}, TTL: 600")
    
    print(f"\n2️⃣  Google OAuth Console:")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   URL: https://console.cloud.google.com/apis/credentials")
    print(f"   ")
    print(f"   Authorized JavaScript origins (add both):")
    print(f"   → https://{domains['customer_portal']}")
    print(f"   → https://{domains['platform_portal']}")
    print(f"   ")
    print(f"   Authorized redirect URIs (add both):")
    print(f"   → https://{domains['customer_portal']}/api/auth/callback")
    print(f"   → https://{domains['platform_portal']}/api/auth/callback")
    
    print(f"\n3️⃣  Access URLs:")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Customer Portal:  https://{domains['customer_portal']}")
    print(f"   Platform Portal:  https://{domains['platform_portal']}")
    print(f"   Backend API:      https://{domains['customer_portal']}/api (or pp domain)")
    print(f"   Health Check:     https://{domains['customer_portal']}/api/health")
    
    print(f"\n4️⃣  Verification:")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   # Check SSL certificates (wait 10-15 mins after DNS)")
    print(f"   gcloud compute ssl-certificates list --project={PROJECT}")
    print(f"   ")
    print(f"   # Test endpoints")
    print(f"   curl https://{domains['customer_portal']}/api/health")
    print(f"   curl https://{domains['platform_portal']}/api/health")
    print(f"   ")
    print(f"   # View backend logs")
    print(f"   gcloud logging read 'resource.labels.service_name=waooaw-api-{environment}' --limit=20 --project={PROJECT}")
    
    print("\n" + "=" * 80)
    print(f"💡 TIP: All {environment} domains use same IP ({STATIC_IP_ADDRESS})")
    print(f"    Load Balancer routes traffic based on hostname!")
    print("=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Deploy WAOOAW infrastructure to GCP",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--environment", "-e",
        required=True,
        choices=ENVIRONMENTS,
        help="Environment to deploy (demo, uat, prod)"
    )
    
    parser.add_argument(
        "--action", "-a",
        required=True,
        choices=ACTIONS,
        help="Action to perform (create, update, delete, preview)"
    )
    
    parser.add_argument(
        "--version", "-v",
        default="latest",
        help="Docker image version tag (default: latest)"
    )
    
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview changes without applying (for update action)"
    )
    
    args = parser.parse_args()
    
    deploy(args.environment, args.action, args.preview, args.version)

if __name__ == "__main__":
    main()

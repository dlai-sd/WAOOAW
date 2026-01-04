# Cloud Infrastructure

Terraform-based infrastructure as code for WAOOAW platform deployment.

## Structure

```
cloud/
├── terraform/              # Terraform IaC configuration (PRIMARY)
│   ├── main.tf            # Root configuration
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Output values
│   ├── generate_tfvars.py # YAML → tfvars generator
│   ├── modules/
│   │   ├── cloud-run/     # Cloud Run v2 services
│   │   ├── networking/    # Serverless NEGs
│   │   └── load-balancer/ # HTTP(S) LB + SSL
│   └── environments/
│       ├── demo.tfvars    # Demo environment variables
│       ├── uat.tfvars     # UAT environment variables
│       └── prod.tfvars    # Production environment variables
├── infrastructure.yaml     # Single source of truth (all environments)
├── demo/                  # Demo environment documentation
├── uat/                   # UAT environment documentation
├── prod/                  # Production environment documentation
├── test/                  # Test scripts
└── cleanup.sh             # GCP resource cleanup utility
```

## Deployment

### Terraform Workflow

```bash
cd cloud/terraform

# 1. Generate tfvars from YAML
python generate_tfvars.py

# 2. Initialize Terraform (first time only)
terraform init

# 3. Validate configuration
terraform validate

# 4. Plan changes
terraform plan -var-file=environments/demo.tfvars

# 5. Apply changes
terraform apply -var-file=environments/demo.tfvars

# 6. Destroy infrastructure (when needed)
terraform destroy -var-file=environments/demo.tfvars
```

### Environment Configuration

Edit `infrastructure.yaml` to configure all environments:

```yaml
project_id: waooaw-oauth
region: asia-south1

environments:
  demo:
    customer_portal_domain: cp.demo.waooaw.com
    platform_portal_domain: pp.demo.waooaw.com
    image_tag: latest
    scaling:
      min_instances: 0
      max_instances: 5
```

Then regenerate tfvars:
```bash
cd terraform
python generate_tfvars.py
```

## Documentation

- **[INFRASTRUCTURE_DEPLOYMENT.md](../INFRASTRUCTURE_DEPLOYMENT.md)** - Complete deployment guide
- **[OAUTH_TESTING_GUIDE.md](../OAUTH_TESTING_GUIDE.md)** - OAuth configuration and testing
- **[V2_CURRENT_STATUS.md](../V2_CURRENT_STATUS.md)** - Current infrastructure status

## Removed Files

All Deployment Manager artifacts (templates/, deploy.py, deploy-gcloud.sh) have been removed.
Terraform is the only supported deployment method.

Historical files archived in `archive/cleanup-2025-01-04/`.

---

**Current Status**: Demo environment fully operational ✅  
**Domains**: https://cp.demo.waooaw.com, https://pp.demo.waooaw.com  
**Backend**: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app  
**Static IP**: 35.190.6.91

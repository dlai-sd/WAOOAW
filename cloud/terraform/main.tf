terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Use local state for now (can migrate to GCS later)
  # backend "gcs" {
  #   bucket = "waooaw-terraform-state"
  #   prefix = "infrastructure"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Static IP (existing, shared across all environments)
data "google_compute_global_address" "static_ip" {
  name = var.static_ip_name
}

# Cloud Run Services
module "backend_api" {
  count  = var.enable_backend_api ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-${var.component}_api-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.backend_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = {
    ENVIRONMENT = var.environment
  }

  secrets = {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  }
}

module "customer_portal" {
  count  = var.enable_customer_portal ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-${var.component}-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "customer-portal"

  image         = var.customer_portal_image
  port          = 8080
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = {
    ENVIRONMENT = var.environment
  }
}

module "platform_portal" {
  count  = var.enable_platform_portal ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-platform-portal-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "platform-portal"

  image         = var.platform_portal_image
  port          = 8080
  cpu           = "1"
  memory        = "1Gi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = {
    ENVIRONMENT = var.environment
  }

  secrets = {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  }
}

locals {
  services = {
    for k, v in {
      api = var.enable_backend_api ? {
        name   = module.backend_api[0].service_name
        region = var.region
      } : null
      customer = var.enable_customer_portal ? {
        name   = module.customer_portal[0].service_name
        region = var.region
      } : null
      platform = var.enable_platform_portal ? {
        name   = module.platform_portal[0].service_name
        region = var.region
      } : null
    } : k => v if v != null
  }
}

# Networking (NEGs for each service)
module "networking" {
  count  = length(local.services) > 0 ? 1 : 0
  source = "./modules/networking"

  environment = var.environment
  region      = var.region
  project_id  = var.project_id
  services    = local.services
}

locals {
  # Convert NEG names (map(string)) to map(object({name, region})) expected by load_balancer
  backend_negs = length(module.networking) > 0 ? {
    for k, v in module.networking[0].neg_names : k => {
      name   = v
      region = var.region
    }
  } : {}
}

# Load Balancer with multi-domain routing
module "load_balancer" {
  count  = length(local.services) > 0 ? 1 : 0
  source = "./modules/load-balancer"

  environment       = var.environment
  project_id        = var.project_id
  static_ip_address = data.google_compute_global_address.static_ip.address
  static_ip_name    = var.static_ip_name

  enable_api      = var.enable_backend_api
  enable_customer = var.enable_customer_portal
  enable_platform = var.enable_platform_portal

  customer_domain = var.domains[var.environment].customer_portal
  platform_domain = var.domains[var.environment].platform_portal

  backend_negs = local.backend_negs

  depends_on = [module.networking[0]]
}

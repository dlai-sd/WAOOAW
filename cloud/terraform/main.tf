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
  source = "./modules/cloud-run"
  
  service_name    = "waooaw-api-${var.environment}"
  region          = var.region
  project_id      = var.project_id
  environment     = var.environment
  service_type    = "backend"
  
  image           = var.backend_image
  port            = 8000
  cpu             = "1"
  memory          = "512Mi"
  min_instances   = var.scaling[var.environment].min
  max_instances   = var.scaling[var.environment].max
  
  env_vars = {
    ENVIRONMENT = var.environment
  }
  
  secrets = {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET          = "JWT_SECRET:latest"
  }
}

module "customer_portal" {
  source = "./modules/cloud-run"
  
  service_name    = "waooaw-portal-${var.environment}"
  region          = var.region
  project_id      = var.project_id
  environment     = var.environment
  service_type    = "customer-portal"
  
  image           = var.customer_portal_image
  port            = 8080
  cpu             = "1"
  memory          = "512Mi"
  min_instances   = var.scaling[var.environment].min
  max_instances   = var.scaling[var.environment].max
  
  env_vars = {
    ENVIRONMENT = var.environment
  }
}

module "platform_portal" {
  source = "./modules/cloud-run"
  
  service_name    = "waooaw-platform-portal-${var.environment}"
  region          = var.region
  project_id      = var.project_id
  environment     = var.environment
  service_type    = "platform-portal"
  
  image           = var.platform_portal_image
  port            = 8080
  cpu             = "1"
  memory          = "1Gi"
  min_instances   = var.scaling[var.environment].min
  max_instances   = var.scaling[var.environment].max
  
  env_vars = {
    ENVIRONMENT = var.environment
  }
  
  secrets = {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET          = "JWT_SECRET:latest"
  }
}

# Networking (NEGs for each service)
module "networking" {
  source = "./modules/networking"
  
  environment = var.environment
  region      = var.region
  project_id  = var.project_id
  
  services = {
    api = {
      name   = module.backend_api.service_name
      region = var.region
    }
    customer = {
      name   = module.customer_portal.service_name
      region = var.region
    }
    platform = {
      name   = module.platform_portal.service_name
      region = var.region
    }
  }
  
  depends_on = [
    module.backend_api,
    module.customer_portal,
    module.platform_portal
  ]
}

# Load Balancer with multi-domain routing
module "load_balancer" {
  source = "./modules/load-balancer"
  
  environment        = var.environment
  project_id         = var.project_id
  static_ip_address  = data.google_compute_global_address.static_ip.address
  static_ip_name     = var.static_ip_name
  
  customer_domain    = var.domains[var.environment].customer_portal
  platform_domain    = var.domains[var.environment].platform_portal
  
  backend_negs = {
    api = {
      name   = module.networking.neg_names.api
      region = var.region
    }
    customer = {
      name   = module.networking.neg_names.customer
      region = var.region
    }
    platform = {
      name   = module.networking.neg_names.platform
      region = var.region
    }
  }
  
  depends_on = [module.networking]
}

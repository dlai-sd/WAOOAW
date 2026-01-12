terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "waooaw-terraform-state"
    prefix = "env" # Will be overridden by -backend-config in workflow
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Static IP (existing, shared across all environments)
data "google_compute_global_address" "static_ip" {
  name = var.static_ip_name
}

# ============================================================================
# CP (Customer Portal) - 3 Services
# ============================================================================

module "cp_frontend" {
  count  = var.enable_cp ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-cp-frontend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "frontend"

  image         = var.cp_frontend_image
  port          = 8080
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = {
    ENVIRONMENT = var.environment
  }
}

module "cp_backend" {
  count  = var.enable_cp ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-cp-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.cp_backend_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = merge(
    {
      ENVIRONMENT = var.environment
    },
    var.enable_plant ? {
      PLANT_API_URL = "https://waooaw-plant-backend-${var.environment}-ryvhxvrdna-el.a.run.app"
    } : {}
  )

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  } : {}

  depends_on = [module.plant_backend]
}

# ============================================================================
# PP (Platform Portal) - 2 Services
# ============================================================================

module "pp_frontend" {
  count  = var.enable_pp ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-pp-frontend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "frontend"

  image         = var.pp_frontend_image
  port          = 8080
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = {
    ENVIRONMENT = var.environment
  }
}

module "pp_backend" {
  count  = var.enable_pp ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-pp-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.pp_backend_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.scaling[var.environment].min
  max_instances = var.scaling[var.environment].max

  env_vars = merge(
    {
      ENVIRONMENT = var.environment
    },
    var.enable_plant ? {
      PLANT_API_URL = "https://waooaw-plant-backend-${var.environment}-ryvhxvrdna-el.a.run.app"
    } : {}
  )

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  } : {}

  depends_on = [module.plant_backend]
}

# ============================================================================
# Plant (Core API) - 1 Service (Backend Only)
# ============================================================================

module "plant_backend" {
  count  = var.enable_plant ? 1 : 0
  source = "./modules/cloud-run"

  service_name = "waooaw-plant-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.plant_backend_image
  port          = 8000
  cpu           = "2" # Higher resources for shared service
  memory        = "1Gi"
  min_instances = var.environment == "demo" ? 0 : 1    # Always-on for uat/prod
  max_instances = var.scaling[var.environment].max * 2 # Can scale higher

  env_vars = {
    ENVIRONMENT = var.environment
  }

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  } : {}
}

# ============================================================================
# Service Collection & Networking
# ============================================================================

locals {
  services = merge(
    # CP Services
    var.enable_cp ? {
      cp_frontend = {
        name   = module.cp_frontend[0].service_name
        region = var.region
      }
      cp_backend = {
        name   = module.cp_backend[0].service_name
        region = var.region
      }
    } : {},
    # PP Services
    var.enable_pp ? {
      pp_frontend = {
        name   = module.pp_frontend[0].service_name
        region = var.region
      }
      pp_backend = {
        name   = module.pp_backend[0].service_name
        region = var.region
      }
    } : {},
    # Plant Services
    var.enable_plant ? {
      plant_backend = {
        name   = module.plant_backend[0].service_name
        region = var.region
      }
    } : {}
  )
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

# Load Balancer with multi-component routing
module "load_balancer" {
  count  = length(local.services) > 0 ? 1 : 0
  source = "./modules/load-balancer"

  environment       = var.environment
  project_id        = var.project_id
  static_ip_address = data.google_compute_global_address.static_ip.address
  static_ip_name    = var.static_ip_name

  enable_cp    = var.enable_cp
  enable_pp    = var.enable_pp
  enable_plant = var.enable_plant

  cp_domain    = var.domains[var.environment].cp
  pp_domain    = var.domains[var.environment].pp
  plant_domain = var.domains[var.environment].plant

  backend_negs = local.backend_negs

  depends_on = [module.networking[0]]
}

# IAM: CP Backend can invoke Plant Backend
resource "google_cloud_run_service_iam_member" "cp_to_plant" {
  count    = var.enable_cp && var.enable_plant ? 1 : 0
  service  = module.plant_backend[0].service_name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${module.cp_backend[0].service_account}"
}

# IAM: PP Backend can invoke Plant Backend
resource "google_cloud_run_service_iam_member" "pp_to_plant" {
  count    = var.enable_pp && var.enable_plant ? 1 : 0
  service  = module.plant_backend[0].service_name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${module.pp_backend[0].service_account}"
}

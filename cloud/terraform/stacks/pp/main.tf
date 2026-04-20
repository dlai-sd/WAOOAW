terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.46"
    }
  }

  backend "gcs" {
    bucket = "waooaw-terraform-state"
    prefix = "env" # overridden by workflow -backend-config
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC Serverless Connector — gives PP backend Cloud Run access to the private
# Memorystore Redis instance (10.53.167.x) per CONTEXT_AND_INDEX.md Redis policy.
# PP backend uses DB /2 (cache).
module "vpc_connector" {
  source = "../../modules/vpc-connector"

  connector_name = "pp-vpc-connector-${var.environment}"
  region         = var.region
  project_id     = var.project_id
  network_id     = var.private_network_id
  ip_cidr_range  = var.vpc_connector_cidr
  min_instances  = 2
  max_instances  = 3
  machine_type   = "e2-micro"
}

module "pp_frontend" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-pp-frontend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "frontend"

  image         = var.pp_frontend_image
  port          = 8080
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    ENVIRONMENT     = var.environment
    PP_API_BASE_URL = local.pp_api_base_url
  }

  # GOOGLE_CLIENT_ID is read at container start by docker-entrypoint.sh and
  # written into pp-runtime-config.js so the SPA can read it at runtime.
  # This avoids baking secrets into the Docker image — same image is promoted
  # through demo → uat → prod by updating only these Cloud Run bindings.
  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID = "GOOGLE_CLIENT_ID:latest"
  } : {}
}

module "pp_backend" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-pp-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.pp_backend_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  vpc_connector_id = module.vpc_connector.connector_id

  env_vars = {
    ENVIRONMENT       = var.environment
    PLANT_GATEWAY_URL = "https://plant.${var.environment}.waooaw.com"
    PLANT_API_URL     = "https://plant.${var.environment}.waooaw.com"

    LOG_LEVEL     = "INFO"
    DEBUG_VERBOSE = "false"

    ENABLE_DB_UPDATES     = var.enable_db_updates
    ALLOWED_EMAIL_DOMAINS = var.allowed_email_domains
    ENABLE_DEV_TOKEN      = var.enable_dev_token
    ENABLE_METERING_DEBUG = var.enable_metering_debug
  }

  secrets = merge(
    var.attach_secret_manager_secrets ? {
      GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
      GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
      JWT_SECRET           = "JWT_SECRET:latest"
    } : {},
    {
      REDIS_URL = "${var.environment}-pp-backend-redis-url:latest"
    }
  )
}

locals {
  # prod uses the canonical domain; other envs use env-prefixed subdomains
  pp_api_base_url = var.environment == "prod" ? "https://platform.waooaw.com/api" : "https://pp.${var.environment}.waooaw.com/api"
}

locals {
  services = {
    pp_frontend = {
      name   = module.pp_frontend.service_name
      region = var.region
    }
    pp_backend = {
      name   = module.pp_backend.service_name
      region = var.region
    }
  }
}

module "networking" {
  source = "../../modules/networking"

  environment = var.environment
  region      = var.region
  project_id  = var.project_id
  services    = local.services

  depends_on = [module.vpc_connector]
}

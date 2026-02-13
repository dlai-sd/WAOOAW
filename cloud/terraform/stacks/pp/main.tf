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
    prefix = "env" # overridden by workflow -backend-config
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
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
    ENVIRONMENT = var.environment
  }
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

  env_vars = {
    ENVIRONMENT       = var.environment
    PLANT_GATEWAY_URL = "https://plant.${var.environment}.waooaw.com"
    PLANT_API_URL     = "https://plant.${var.environment}.waooaw.com"

    LOG_LEVEL     = "INFO"
    DEBUG_VERBOSE = "false"

    # DB Updates are break-glass admin tooling.
    # Demo: enabled for smoke tests.
    # Prod: enabled for controlled direct DB operations.
    ENABLE_DB_UPDATES = (var.environment == "demo" || var.environment == "prod") ? "true" : "false"

    # Demo environment is used for smoke tests; allow common Google domains.
    # Prod/uat remain restricted by default.
    ALLOWED_EMAIL_DOMAINS = var.environment == "demo" ? "dlaisd.com,waooaw.com,gmail.com,googlemail.com" : "dlaisd.com,waooaw.com"
  }

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  } : {}
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
}

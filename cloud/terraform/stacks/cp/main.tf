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

module "cp_frontend" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-cp-frontend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "frontend"

  image         = var.cp_frontend_image
  port          = 8080
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    ENVIRONMENT     = var.environment
    CP_API_BASE_URL = local.cp_api_base_url
  }

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID   = "GOOGLE_CLIENT_ID:latest"
    TURNSTILE_SITE_KEY = "TURNSTILE_SITE_KEY:latest"
  } : {}
}

module "cp_backend" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-cp-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.cp_backend_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    ENVIRONMENT              = var.environment
    PLANT_GATEWAY_URL        = local.plant_gateway_url
    OTP_DELIVERY_MODE        = var.otp_delivery_mode != "" ? var.otp_delivery_mode : (var.environment == "demo" ? "disabled" : "provider")
    CP_OTP_DELIVERY_PROVIDER = var.cp_otp_delivery_provider != "" ? var.cp_otp_delivery_provider : "smtp"
  }

  # CP_REGISTRATION_KEY is required for CP→Plant customer upsert.
  # Attach it even when `attach_secret_manager_secrets=false` so demo can
  # persist customers into Plant without requiring all other secrets.
  secrets = merge(
    var.attach_secret_manager_secrets ? {
      GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
      GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
      JWT_SECRET           = "JWT_SECRET:latest"
      TURNSTILE_SECRET_KEY = "TURNSTILE_SECRET_KEY:latest"
    } : {},
    {
      CP_REGISTRATION_KEY = "CP_REGISTRATION_KEY:latest"
    }
  )
}

locals {
  cp_api_base_url   = var.environment == "prod" ? "https://cp.waooaw.com/api" : "https://cp.${var.environment}.waooaw.com/api"
  plant_gateway_url = var.environment == "prod" ? "https://plant.waooaw.com" : "https://plant.${var.environment}.waooaw.com"
}

locals {
  services = {
    cp_frontend = {
      name   = module.cp_frontend.service_name
      region = var.region
    }
    cp_backend = {
      name   = module.cp_backend.service_name
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

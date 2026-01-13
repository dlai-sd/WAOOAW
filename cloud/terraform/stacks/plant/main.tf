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

module "plant_backend" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-plant-backend-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.plant_backend_image
  port          = 8000
  cpu           = "2"
  memory        = "1Gi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    ENVIRONMENT = var.environment
  }

  secrets = var.attach_secret_manager_secrets ? {
    GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
    GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
    JWT_SECRET           = "JWT_SECRET:latest"
  } : {}
}

locals {
  services = {
    plant_backend = {
      name   = module.plant_backend.service_name
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

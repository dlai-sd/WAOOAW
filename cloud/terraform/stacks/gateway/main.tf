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

module "cp_gateway" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-gateway-cp-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image_uri     = "${var.artifact_registry}/waooaw/gateway-cp:${var.image_tag}"
  port          = 8000
  cpu           = "2000m"
  memory        = "1Gi"
  min_instances = 1
  max_instances = 10
  timeout       = 300
  concurrency   = 80

  env_vars = {
    ENVIRONMENT  = var.environment
    PORT         = "8000"
    GATEWAY_TYPE = "CP"
    JWT_ISSUER   = "waooaw.com"
  }

  secrets = {
    DATABASE_URL         = "${var.environment}-plant-database-url"
    JWT_PUBLIC_KEY       = "${var.environment}-jwt-public-key"
    LAUNCHDARKLY_SDK_KEY = "${var.environment}-launchdarkly-sdk-key:latest"
  }

  depends_on_services = []
}

module "pp_gateway" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-gateway-pp-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image_uri     = "${var.artifact_registry}/waooaw/gateway-pp:${var.image_tag}"
  port          = 8001
  cpu           = "2000m"
  memory        = "1Gi"
  min_instances = 1
  max_instances = 10
  timeout       = 300
  concurrency   = 80

  env_vars = {
    ENVIRONMENT  = var.environment
    PORT         = "8001"
    GATEWAY_TYPE = "PP"
    JWT_ISSUER   = "waooaw.com"
  }

  secrets = {
    DATABASE_URL         = "${var.environment}-plant-database-url"
    JWT_PUBLIC_KEY       = "${var.environment}-jwt-public-key"
    LAUNCHDARKLY_SDK_KEY = "${var.environment}-launchdarkly-sdk-key:latest"
  }

  depends_on_services = []
}

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

data "google_project" "current" {
  project_id = var.project_id
}

locals {
  # Cloud Run uses the default compute service account when no service account is set.
  default_compute_sa = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"

  # Prefer the actual Plant Gateway service account if it is set; otherwise fall back.
  plant_gateway_sa = try(module.plant_gateway.service_account, null) != null && try(module.plant_gateway.service_account, "") != "" ? module.plant_gateway.service_account : local.default_compute_sa
}

# Cloud SQL PostgreSQL Database
module "plant_database" {
  source = "../../modules/cloud-sql"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  instance_name       = "plant-sql-${var.environment}"
  database_version    = "POSTGRES_15"
  tier                = var.db_tier
  availability_type   = var.db_availability_type
  disk_size_gb        = var.db_disk_size_gb
  enable_pitr         = var.db_enable_pitr
  max_connections     = var.db_max_connections
  private_network_id  = var.private_network_id
  database_name       = "plant"
  database_user       = "plant_app"
  database_password   = var.database_password
  deletion_protection = var.db_deletion_protection
}

# VPC Serverless Connector for Cloud Run to access private Cloud SQL
module "vpc_connector" {
  source = "../../modules/vpc-connector"

  connector_name = "plant-vpc-connector-${var.environment}"
  region         = var.region
  project_id     = var.project_id
  network_id     = var.private_network_id
  ip_cidr_range  = var.vpc_connector_cidr # Must not overlap with Cloud SQL (10.19.0.0/16)
  min_instances  = 2
  max_instances  = 3
  machine_type   = "e2-micro"
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

  # Plant backend should not be publicly invokable; access is mediated by the Plant Gateway.
  # Note: We keep ingress open but lock invocation via IAM (no allUsers invoker).
  ingress               = "INGRESS_TRAFFIC_ALL"
  allow_unauthenticated = false

  cloud_sql_connection_name = module.plant_database.instance_connection_name
  vpc_connector_id          = module.vpc_connector.connector_id

  env_vars = {
    ENVIRONMENT               = var.environment
    CLOUD_SQL_CONNECTION_NAME = module.plant_database.instance_connection_name
    LOG_LEVEL                 = "info"
    DEBUG_VERBOSE             = "false"

    # DB Updates are break-glass admin tooling.
    # Demo/UAT: enabled for testing and controlled operations.
    # Prod: disabled for safety.
    ENABLE_DB_UPDATES = (var.environment == "demo" || var.environment == "uat") ? "true" : "false"
  }

  secrets = var.attach_secret_manager_secrets ? merge(
    {
      GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
      GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
      JWT_SECRET           = "JWT_SECRET:latest"
    },
    {
      DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
    }
    ) : {
    DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
  }

  depends_on = [module.plant_database, module.vpc_connector]
}

# Allow the runtime service account (default compute SA) to invoke Plant Backend.
# Plant Gateway runs under the same SA unless overridden.
resource "google_cloud_run_v2_service_iam_member" "plant_backend_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.plant_backend.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.plant_gateway_sa}"
}

# Plant Gateway (FastAPI proxy with middleware)
module "plant_gateway" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-plant-gateway-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  image         = var.plant_gateway_image
  port          = 8000
  cpu           = "1"
  memory        = "512Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  # Gateway does not require DB/VPC access; keep it off the VPC connector so
  # Cloud Run metadata-based ID token minting cannot be impacted by egress routing.
  cloud_sql_connection_name = null
  vpc_connector_id          = null

  env_vars = {
    ENVIRONMENT                = var.environment
    PLANT_BACKEND_URL          = module.plant_backend.service_url
    PLANT_BACKEND_USE_ID_TOKEN = "true"
    PLANT_BACKEND_AUDIENCE     = module.plant_backend.service_url
    LOG_LEVEL                  = "info"
    DEBUG_VERBOSE              = "false"
    OPA_URL                    = "https://opa-policy-engine.a.run.app" # TODO: Create OPA service
    OPA_SERVICE_URL            = "https://opa-policy-engine.a.run.app" # Back-compat for older configs
    REDIS_HOST                 = "10.0.0.3"                            # TODO: Create Redis instance
    CLOUD_SQL_CONNECTION_NAME  = module.plant_database.instance_connection_name
    JWT_ISSUER                 = "waooaw.com"
    JWT_ALGORITHM              = "HS256"
  }

  # CP_REGISTRATION_KEY gates /api/v1/customers on the Gateway; without it,
  # CP registrations won't persist into Plant's DB (customer_entity).
  secrets = merge(
    var.attach_secret_manager_secrets ? {
      DATABASE_URL   = "${module.plant_database.database_url_secret_id}:latest"
      JWT_SECRET     = "JWT_SECRET:latest"
      JWT_PUBLIC_KEY = "JWT_SECRET:latest"
    } : {
      DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
    },
    {
      CP_REGISTRATION_KEY = "CP_REGISTRATION_KEY:latest"
    }
  )

  depends_on = [module.plant_database, module.vpc_connector, module.plant_backend]
}

locals {
  services = {
    plant_backend = {
      name   = module.plant_backend.service_name
      region = var.region
    }
    plant_gateway = {
      name   = module.plant_gateway.service_name
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

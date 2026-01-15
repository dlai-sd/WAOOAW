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

  cloud_sql_connection_name = module.plant_database.instance_connection_name

  env_vars = {
    ENVIRONMENT               = var.environment
    CLOUD_SQL_CONNECTION_NAME = module.plant_database.instance_connection_name
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

  depends_on = [module.plant_database]
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

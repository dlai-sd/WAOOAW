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

  cloud_sql_connection_name = module.plant_database.instance_connection_name
  vpc_connector_id          = module.vpc_connector.connector_id

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

  depends_on = [module.plant_database, module.vpc_connector]
}

# Cloud Run Job for Database Migrations
module "plant_db_migration_job" {
  source = "../../modules/cloud-run-job"

  job_name                  = "plant-db-migrations-${var.environment}"
  region                    = var.region
  project_id                = var.project_id
  image                     = var.plant_migration_image
  vpc_connector_id          = module.vpc_connector.connector_id
  cloud_sql_connection_name = module.plant_database.instance_connection_name
  service_account_email     = module.plant_backend.service_account_email

  cpu            = "1"
  memory         = "512Mi"
  timeout_seconds = 600
  max_retries    = 0

  env_vars = {
    ENVIRONMENT               = var.environment
    CLOUD_SQL_CONNECTION_NAME = module.plant_database.instance_connection_name
  }

  secrets = {
    DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
  }

  depends_on = [module.plant_database, module.vpc_connector]
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

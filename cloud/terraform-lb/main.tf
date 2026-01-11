terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Static IP (existing)
data "google_compute_global_address" "static_ip" {
  name = var.static_ip_name
}

# Deterministic NEG names (created in app state)
locals {
  backend_negs = {
    for k, enabled in {
      api      : var.enable_backend_api,
      customer : var.enable_customer_portal,
      platform : var.enable_platform_portal,
    } : k => {
      name   = "waooaw-${var.environment}-${k}-neg"
      region = var.region
    } if enabled
  }
}

module "load_balancer" {
  source = "../modules/load-balancer"

  environment       = var.environment
  project_id        = var.project_id
  static_ip_address = data.google_compute_global_address.static_ip.address
  static_ip_name    = var.static_ip_name

  enable_api      = var.enable_backend_api
  enable_customer = var.enable_customer_portal
  enable_platform = var.enable_platform_portal

  customer_domain = var.domains[var.environment].customer_portal
  platform_domain = var.domains[var.environment].platform_portal

  backend_negs = local.backend_negs
}

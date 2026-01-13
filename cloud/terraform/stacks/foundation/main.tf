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
    prefix = "foundation" # overridden by workflow -backend-config (kept explicit)
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

check "at_least_one_component_enabled" {
  assert {
    condition     = var.enable_cp || var.enable_pp || var.enable_plant
    error_message = "At least one of enable_cp, enable_pp, or enable_plant must be true."
  }
}

data "google_compute_global_address" "static_ip" {
  name = var.static_ip_name
}

# Pull serverless NEG names from app stacks (remote state).
# These state objects must exist before foundation can be planned/applied.

data "terraform_remote_state" "cp_demo" {
  count   = (var.enable_cp && contains(var.enabled_environments, "demo")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/demo/cp"
  }
}

data "terraform_remote_state" "cp_uat" {
  count   = (var.enable_cp && contains(var.enabled_environments, "uat")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/uat/cp"
  }
}

data "terraform_remote_state" "cp_prod" {
  count   = (var.enable_cp && contains(var.enabled_environments, "prod")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/prod/cp"
  }
}

data "terraform_remote_state" "pp_demo" {
  count   = (var.enable_pp && contains(var.enabled_environments, "demo")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/demo/pp"
  }
}

data "terraform_remote_state" "pp_uat" {
  count   = (var.enable_pp && contains(var.enabled_environments, "uat")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/uat/pp"
  }
}

data "terraform_remote_state" "pp_prod" {
  count   = (var.enable_pp && contains(var.enabled_environments, "prod")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/prod/pp"
  }
}

data "terraform_remote_state" "plant_demo" {
  count   = (var.enable_plant && contains(var.enabled_environments, "demo")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/demo/plant"
  }
}

data "terraform_remote_state" "plant_uat" {
  count   = (var.enable_plant && contains(var.enabled_environments, "uat")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/uat/plant"
  }
}

data "terraform_remote_state" "plant_prod" {
  count   = (var.enable_plant && contains(var.enabled_environments, "prod")) ? 1 : 0
  backend = "gcs"
  config = {
    bucket = "waooaw-terraform-state"
    prefix = "env/prod/plant"
  }
}

locals {
  cp_demo_enabled    = var.enable_cp && contains(var.enabled_environments, "demo")
  cp_uat_enabled     = var.enable_cp && contains(var.enabled_environments, "uat")
  cp_prod_enabled    = var.enable_cp && contains(var.enabled_environments, "prod")
  pp_demo_enabled    = var.enable_pp && contains(var.enabled_environments, "demo")
  pp_uat_enabled     = var.enable_pp && contains(var.enabled_environments, "uat")
  pp_prod_enabled    = var.enable_pp && contains(var.enabled_environments, "prod")
  plant_demo_enabled = var.enable_plant && contains(var.enabled_environments, "demo")
  plant_uat_enabled  = var.enable_plant && contains(var.enabled_environments, "uat")
  plant_prod_enabled = var.enable_plant && contains(var.enabled_environments, "prod")

  # Convenience accessor: state outputs.backend_negs is map(string->object({name,region}))
  cp_demo_negs    = local.cp_demo_enabled ? data.terraform_remote_state.cp_demo[0].outputs.backend_negs : {}
  cp_uat_negs     = local.cp_uat_enabled ? data.terraform_remote_state.cp_uat[0].outputs.backend_negs : {}
  cp_prod_negs    = local.cp_prod_enabled ? data.terraform_remote_state.cp_prod[0].outputs.backend_negs : {}
  pp_demo_negs    = local.pp_demo_enabled ? data.terraform_remote_state.pp_demo[0].outputs.backend_negs : {}
  pp_uat_negs     = local.pp_uat_enabled ? data.terraform_remote_state.pp_uat[0].outputs.backend_negs : {}
  pp_prod_negs    = local.pp_prod_enabled ? data.terraform_remote_state.pp_prod[0].outputs.backend_negs : {}
  plant_demo_negs = local.plant_demo_enabled ? data.terraform_remote_state.plant_demo[0].outputs.backend_negs : {}
  plant_uat_negs  = local.plant_uat_enabled ? data.terraform_remote_state.plant_uat[0].outputs.backend_negs : {}
  plant_prod_negs = local.plant_prod_enabled ? data.terraform_remote_state.plant_prod[0].outputs.backend_negs : {}

  backends = merge(
    local.cp_demo_enabled ? {
      cp_demo_frontend = local.cp_demo_negs["cp_frontend"]
      cp_demo_backend  = local.cp_demo_negs["cp_backend"]
    } : {},
    local.cp_uat_enabled ? {
      cp_uat_frontend = local.cp_uat_negs["cp_frontend"]
      cp_uat_backend  = local.cp_uat_negs["cp_backend"]
    } : {},
    local.cp_prod_enabled ? {
      cp_prod_frontend = local.cp_prod_negs["cp_frontend"]
      cp_prod_backend  = local.cp_prod_negs["cp_backend"]
    } : {},
    local.pp_demo_enabled ? {
      pp_demo_frontend = local.pp_demo_negs["pp_frontend"]
      pp_demo_backend  = local.pp_demo_negs["pp_backend"]
    } : {},
    local.pp_uat_enabled ? {
      pp_uat_frontend = local.pp_uat_negs["pp_frontend"]
      pp_uat_backend  = local.pp_uat_negs["pp_backend"]
    } : {},
    local.pp_prod_enabled ? {
      pp_prod_frontend = local.pp_prod_negs["pp_frontend"]
      pp_prod_backend  = local.pp_prod_negs["pp_backend"]
    } : {},
    local.plant_demo_enabled ? {
      plant_demo_backend = local.plant_demo_negs["plant_backend"]
    } : {},
    local.plant_uat_enabled ? {
      plant_uat_backend = local.plant_uat_negs["plant_backend"]
    } : {},
    local.plant_prod_enabled ? {
      plant_prod_backend = local.plant_prod_negs["plant_backend"]
    } : {}
  )

  hosts = merge(
    local.cp_demo_enabled ? {
      (var.domains.demo.cp) = {
        default_backend_key = "cp_demo_frontend"
        api_backend_key     = "cp_demo_backend"
        include_api         = true
      }
    } : {},
    local.cp_uat_enabled ? {
      (var.domains.uat.cp) = {
        default_backend_key = "cp_uat_frontend"
        api_backend_key     = "cp_uat_backend"
        include_api         = true
      }
    } : {},
    local.cp_prod_enabled ? {
      (var.domains.prod.cp) = {
        default_backend_key = "cp_prod_frontend"
        api_backend_key     = "cp_prod_backend"
        include_api         = true
      }
    } : {},
    local.pp_demo_enabled ? {
      (var.domains.demo.pp) = {
        default_backend_key = "pp_demo_frontend"
        api_backend_key     = "pp_demo_backend"
        include_api         = true
      }
    } : {},
    local.pp_uat_enabled ? {
      (var.domains.uat.pp) = {
        default_backend_key = "pp_uat_frontend"
        api_backend_key     = "pp_uat_backend"
        include_api         = true
      }
    } : {},
    local.pp_prod_enabled ? {
      (var.domains.prod.pp) = {
        default_backend_key = "pp_prod_frontend"
        api_backend_key     = "pp_prod_backend"
        include_api         = true
      }
    } : {},
    local.plant_demo_enabled ? {
      (var.domains.demo.plant) = {
        default_backend_key = "plant_demo_backend"
        api_backend_key     = "plant_demo_backend"
        include_api         = false
      }
    } : {},
    local.plant_uat_enabled ? {
      (var.domains.uat.plant) = {
        default_backend_key = "plant_uat_backend"
        api_backend_key     = "plant_uat_backend"
        include_api         = false
      }
    } : {},
    local.plant_prod_enabled ? {
      (var.domains.prod.plant) = {
        default_backend_key = "plant_prod_backend"
        api_backend_key     = "plant_prod_backend"
        include_api         = false
      }
    } : {}
  )

  all_domains = sort(keys(local.hosts))

  # Compute hash of domains to use in cert name (forces new cert when domains change)
  domain_hash = substr(md5(join(",", local.all_domains)), 0, 8)

  # Default backend must exist; pick the first hostname.
  # A separate check ensures we never index into an empty list.

  # Default backend must exist; pick the first hostname.
  default_backend_key = local.all_domains[0]

  host_matchers = {
    for host, cfg in local.hosts : host => {
      matcher_name = replace(replace(host, ".", "-"), "*", "wildcard")
      cfg          = cfg
    }
  }
}

check "at_least_one_hostname" {
  assert {
    condition     = length(local.all_domains) > 0
    error_message = "No hostnames are enabled. Check enabled_environments and enable_* toggles."
  }
}

resource "google_compute_backend_service" "service" {
  for_each = local.backends

  name                  = "shared-${replace(each.key, "_", "-")}-backend"
  project               = var.project_id
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = 30
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group           = "projects/${var.project_id}/regions/${each.value.region}/networkEndpointGroups/${each.value.name}"
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [timeout_sec, log_config]
  }
}

resource "google_compute_url_map" "main" {
  name    = "waooaw-shared-url-map"
  project = var.project_id

  default_service = google_compute_backend_service.service[local.hosts[local.all_domains[0]].default_backend_key].id

  dynamic "host_rule" {
    for_each = local.host_matchers
    content {
      hosts        = [host_rule.key]
      path_matcher = host_rule.value.matcher_name
    }
  }

  dynamic "path_matcher" {
    for_each = local.host_matchers
    content {
      name            = path_matcher.value.matcher_name
      default_service = google_compute_backend_service.service[path_matcher.value.cfg.default_backend_key].id

      dynamic "path_rule" {
        for_each = concat(
          path_matcher.value.cfg.include_api ? [{
            paths   = ["/api/*"]
            backend = path_matcher.value.cfg.api_backend_key
          }] : [],
          [{
            paths   = ["/health"]
            backend = path_matcher.value.cfg.api_backend_key
          }]
        )
        content {
          paths   = path_rule.value.paths
          service = google_compute_backend_service.service[path_rule.value.backend].id
        }
      }
    }
  }
}

resource "google_compute_url_map" "http_redirect" {
  name    = "waooaw-shared-http-redirect"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

# Grouped SAN cert for all hostnames.
# NOTE: This is intentionally grouped for now. As environments grow, we can
# switch to per-host managed certs (one cert per hostname) to reduce blast
# radius for cert renewals/provisioning.
resource "google_compute_managed_ssl_certificate" "shared" {
  name    = "waooaw-shared-ssl-${local.domain_hash}"
  project = var.project_id

  managed {
    domains = local.all_domains
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_target_https_proxy" "main" {
  name             = "waooaw-shared-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.main.id
  ssl_certificates = [google_compute_managed_ssl_certificate.shared.id]

  quic_override = "ENABLE"

}

resource "google_compute_target_http_proxy" "redirect" {
  name    = "waooaw-shared-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "https" {
  name                  = "waooaw-shared-https-forwarding"
  project               = var.project_id
  ip_address            = data.google_compute_global_address.static_ip.address
  ip_protocol           = "TCP"
  port_range            = "443"
  target                = google_compute_target_https_proxy.main.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "waooaw-shared-http-forwarding"
  project               = var.project_id
  ip_address            = data.google_compute_global_address.static_ip.address
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

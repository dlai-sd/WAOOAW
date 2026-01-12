# Health Checks (conditional, one per service)

# CP Component Health Checks
resource "google_compute_health_check" "cp_frontend" {
  count   = var.enable_cp ? 1 : 0
  name    = "${var.environment}-cp-frontend-health"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  lifecycle {
    ignore_changes = [
      check_interval_sec,
      timeout_sec,
      healthy_threshold,
      unhealthy_threshold
    ]
  }
}

resource "google_compute_health_check" "cp_backend" {
  count   = var.enable_cp ? 1 : 0
  name    = "${var.environment}-cp-backend-health"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/health"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  lifecycle {
    ignore_changes = [
      check_interval_sec,
      timeout_sec,
      healthy_threshold,
      unhealthy_threshold
    ]
  }
}



# PP Component Health Checks
resource "google_compute_health_check" "pp_frontend" {
  count   = var.enable_pp ? 1 : 0
  name    = "${var.environment}-pp-frontend-health"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  lifecycle {
    ignore_changes = [
      check_interval_sec,
      timeout_sec,
      healthy_threshold,
      unhealthy_threshold
    ]
  }
}

resource "google_compute_health_check" "pp_backend" {
  count   = var.enable_pp ? 1 : 0
  name    = "${var.environment}-pp-backend-health"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/health"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  lifecycle {
    ignore_changes = [
      check_interval_sec,
      timeout_sec,
      healthy_threshold,
      unhealthy_threshold
    ]
  }
}



# Plant Component Health Checks
resource "google_compute_health_check" "plant_backend" {
  count   = var.enable_plant ? 1 : 0
  name    = "${var.environment}-plant-backend-health"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/health"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3

  lifecycle {
    ignore_changes = [
      check_interval_sec,
      timeout_sec,
      healthy_threshold,
      unhealthy_threshold
    ]
  }
}



# Backend Services (conditional, one per service)

# CP Component Backend Services
resource "google_compute_backend_service" "cp_frontend" {
  count       = var.enable_cp ? 1 : 0
  name        = "${var.environment}-cp-frontend-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "cp_frontend") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["cp_frontend"].region}/networkEndpointGroups/${var.backend_negs["cp_frontend"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [
      timeout_sec,
      log_config
    ]
  }
}

resource "google_compute_backend_service" "cp_backend" {
  count       = var.enable_cp ? 1 : 0
  name        = "${var.environment}-cp-backend-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "cp_backend") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["cp_backend"].region}/networkEndpointGroups/${var.backend_negs["cp_backend"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [
      timeout_sec,
      log_config
    ]
  }
}



# PP Component Backend Services
resource "google_compute_backend_service" "pp_frontend" {
  count       = var.enable_pp ? 1 : 0
  name        = "${var.environment}-pp-frontend-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "pp_frontend") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["pp_frontend"].region}/networkEndpointGroups/${var.backend_negs["pp_frontend"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [
      timeout_sec,
      log_config
    ]
  }
}

resource "google_compute_backend_service" "pp_backend" {
  count       = var.enable_pp ? 1 : 0
  name        = "${var.environment}-pp-backend-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "pp_backend") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["pp_backend"].region}/networkEndpointGroups/${var.backend_negs["pp_backend"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [
      timeout_sec,
      log_config
    ]
  }
}



# Plant Component Backend Services
resource "google_compute_backend_service" "plant_backend" {
  count       = var.enable_plant ? 1 : 0
  name        = "${var.environment}-plant-backend-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "plant_backend") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["plant_backend"].region}/networkEndpointGroups/${var.backend_negs["plant_backend"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  lifecycle {
    ignore_changes = [
      timeout_sec,
      log_config
    ]
  }
}



# URL Map with conditional host rules and path routing
locals {
  # Determine default backend service (at least one must be enabled)
  # Priority: cp_frontend > pp_frontend > plant_backend
  default_backend = (
    length(google_compute_backend_service.cp_frontend) > 0 ? google_compute_backend_service.cp_frontend[0].id :
    length(google_compute_backend_service.pp_frontend) > 0 ? google_compute_backend_service.pp_frontend[0].id :
    length(google_compute_backend_service.plant_backend) > 0 ? google_compute_backend_service.plant_backend[0].id :
    null # Should never happen - at least one service must be enabled
  )

  # Collect all SSL certificates for HTTPS proxy
  ssl_certs = concat(
    length(google_compute_managed_ssl_certificate.cp) > 0 ? [google_compute_managed_ssl_certificate.cp[0].id] : [],
    length(google_compute_managed_ssl_certificate.pp) > 0 ? [google_compute_managed_ssl_certificate.pp[0].id] : [],
    length(google_compute_managed_ssl_certificate.plant) > 0 ? [google_compute_managed_ssl_certificate.plant[0].id] : []
  )
}

resource "google_compute_url_map" "main" {
  name            = "${var.environment}-url-map"
  project         = var.project_id
  default_service = local.default_backend

  # CP Component Routing
  dynamic "host_rule" {
    for_each = var.enable_cp ? [1] : []
    content {
      hosts        = [var.cp_domain]
      path_matcher = "cp-matcher"
    }
  }

  dynamic "path_matcher" {
    for_each = var.enable_cp ? [1] : []
    content {
      name            = "cp-matcher"
      default_service = google_compute_backend_service.cp_frontend[0].id

      # Route /api/* to CP backend
      path_rule {
        paths   = ["/api/*"]
        service = google_compute_backend_service.cp_backend[0].id
      }

      # Route /health to CP backend
      path_rule {
        paths   = ["/health"]
        service = google_compute_backend_service.cp_backend[0].id
      }
    }
  }

  # PP Component Routing
  dynamic "host_rule" {
    for_each = var.enable_pp ? [1] : []
    content {
      hosts        = [var.pp_domain]
      path_matcher = "pp-matcher"
    }
  }

  dynamic "path_matcher" {
    for_each = var.enable_pp ? [1] : []
    content {
      name            = "pp-matcher"
      default_service = google_compute_backend_service.pp_frontend[0].id

      # Route /api/* to PP backend
      path_rule {
        paths   = ["/api/*"]
        service = google_compute_backend_service.pp_backend[0].id
      }

      # Route /health to PP backend
      path_rule {
        paths   = ["/health"]
        service = google_compute_backend_service.pp_backend[0].id
      }
    }
  }

  # Plant Component Routing (backend and health only, no frontend)
  dynamic "host_rule" {
    for_each = var.enable_plant ? [1] : []
    content {
      hosts        = [var.plant_domain]
      path_matcher = "plant-matcher"
    }
  }

  dynamic "path_matcher" {
    for_each = var.enable_plant ? [1] : []
    content {
      name            = "plant-matcher"
      default_service = google_compute_backend_service.plant_backend[0].id

      # Route /health explicitly to Plant backend
      path_rule {
        paths   = ["/health"]
        service = google_compute_backend_service.plant_backend[0].id
      }
    }
  }
}

# HTTP to HTTPS redirect
resource "google_compute_url_map" "http_redirect" {
  name    = "${var.environment}-http-redirect-map"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }

  lifecycle {
    ignore_changes = [default_url_redirect]
  }
}

# SSL Certificates (conditional, one per component)
resource "google_compute_managed_ssl_certificate" "cp" {
  count   = var.enable_cp ? 1 : 0
  name    = "${var.environment}-cp-ssl"
  project = var.project_id

  managed {
    domains = [var.cp_domain]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_managed_ssl_certificate" "pp" {
  count   = var.enable_pp ? 1 : 0
  name    = "${var.environment}-pp-ssl"
  project = var.project_id

  managed {
    domains = [var.pp_domain]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_managed_ssl_certificate" "plant" {
  count   = var.enable_plant ? 1 : 0
  name    = "${var.environment}-plant-ssl"
  project = var.project_id

  managed {
    domains = [var.plant_domain]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# HTTPS Proxy (only create if we have SSL certs)
resource "google_compute_target_https_proxy" "main" {
  count            = length(local.ssl_certs) > 0 ? 1 : 0
  name             = "${var.environment}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.main.id
  ssl_certificates = local.ssl_certs

  quic_override = "ENABLE"

  lifecycle {
    ignore_changes = [ssl_certificates]
  }
}

# HTTP Proxy (for redirect)
resource "google_compute_target_http_proxy" "redirect" {
  name    = "${var.environment}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

# Forwarding Rules
resource "google_compute_global_forwarding_rule" "https" {
  count                 = length(local.ssl_certs) > 0 ? 1 : 0
  name                  = "${var.environment}-https-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_address
  ip_protocol           = "TCP"
  port_range            = "443"
  target                = google_compute_target_https_proxy.main[0].id
  load_balancing_scheme = "EXTERNAL_MANAGED"

  lifecycle {
    ignore_changes = [target]
  }
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.environment}-http-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_address
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
  load_balancing_scheme = "EXTERNAL_MANAGED"

  lifecycle {
    ignore_changes = [target]
  }
}

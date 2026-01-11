# Health Checks (conditional)
resource "google_compute_health_check" "api" {
  count   = var.enable_api ? 1 : 0
  name    = "${var.environment}-api-health-check"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/health"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}

resource "google_compute_health_check" "customer" {
  count   = var.enable_customer ? 1 : 0
  name    = "${var.environment}-customer-health-check"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}

resource "google_compute_health_check" "platform" {
  count   = var.enable_platform ? 1 : 0
  name    = "${var.environment}-platform-health-check"
  project = var.project_id

  https_health_check {
    port         = 443
    request_path = "/"
  }

  check_interval_sec  = 10
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}

# Backend Services (conditional)
resource "google_compute_backend_service" "api" {
  count       = var.enable_api ? 1 : 0
  name        = "${var.environment}-api-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"
  health_checks         = [google_compute_health_check.api[0].id]

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "api") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["api"].region}/networkEndpointGroups/${var.backend_negs["api"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "customer" {
  count       = var.enable_customer ? 1 : 0
  name        = "${var.environment}-customer-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  load_balancing_scheme = "EXTERNAL_MANAGED"
  health_checks         = [google_compute_health_check.customer[0].id]

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "customer") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["customer"].region}/networkEndpointGroups/${var.backend_negs["customer"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "platform" {
  count       = var.enable_platform ? 1 : 0
  name        = "${var.environment}-platform-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30

  dynamic "backend" {
    for_each = contains(keys(var.backend_negs), "platform") ? [1] : []
    content {
      group           = "projects/${var.project_id}/regions/${var.backend_negs["platform"].region}/networkEndpointGroups/${var.backend_negs["platform"].name}"
      balancing_mode  = "UTILIZATION"
      capacity_scaler = 1.0
    }
    group           = "projects/${var.project_id}/regions/${var.backend_negs["platform"].region}/networkEndpointGroups/${var.backend_negs["platform"].name}"
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}
# Prioritize customer portal, fallback to API backend (at least one must be enabled)
  customer_default = var.enable_customer ? google_compute_backend_service.customer[0].id : google_compute_backend_service.api[0].id
  
  # Collect all SSL certificates for HTTPS proxy
  ssl_certs = concat(
    var.enable_customer ? [google_compute_managed_ssl_certificate.customer[0].id] : [],
    var.enable_platform ? [google_compute_managed_ssl_certificate.platform[0].id] : []
locals {
  customer_default = var.enable_customer ? google_compute_backend_service.customer[0].id : (
    var.enable_api ? google_compute_backend_service.api[0].id : ""
  )
}

resource "google_compute_url_map" "main" {
  name            = "${var.environment}-url-map"
  project         = var.project_id
  default_service = local.customer_default

  dynamic "host_rule" {
    for_each = var.enable_customer ? [1] : []
    content {
      hosts        = [var.customer_domain]
      path_matcher = "customer-matcher"
    }
  }

  dynamic "host_rule" {
    for_each = var.enable_platform ? [1] : []
    content {
      hosts        = [var.platform_domain]
      path_matcher = "platform-matcher"
    }
  }

  dynamic "path_matcher" {
    for_each = var.enable_customer ? [1] : []
    content {
      name            = "customer-matcher"
      default_service = google_compute_backend_service.customer[0].id

      dynamic "path_rule" {
        for_each = var.enable_api ? [1] : []
        content {
          paths   = ["/api/*", "/auth/*", "/health"]
          service = google_compute_backend_service.api[0].id
        }
      }
    }
  }

  dynamic "path_matcher" {
    for_each = var.enable_platform ? [1] : []
    content {
      name            = "platform-matcher"
      default_service = google_compute_backend_service.platform[0].id

      dynamic "path_rule" {
        for_each = var.enable_api ? [1] : []
        content {
          paths   = ["/api/*", "/auth/*", "/health"]
          service = google_compute_backend_service.api[0].id
        }
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
}

# SSL Certificates (conditional)
resource "google_compute_managed_ssl_certificate" "customer" {
  count   = var.enable_customer ? 1 : 0
  name    = "${var.environment}-customer-ssl"
  project = var.project_id

  managed {
    domains = [var.customer_domain]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_managed_ssl_certificate" "platform" {
  count   = var.enable_platform ? 1 : 0
  name    = "${var.environment}-platform-ssl"
  project = var.project_id

  managed {
    domains = (only create if we have SSL certs)
resource "google_compute_target_https_proxy" "main" {
  count            = length(local.ssl_certs) > 0 ? 1 : 0
locals {
  ssl_certs = concat(
    var.enable_customer ? [google_compute_managed_ssl_certificate.customer[0].id] : [],
    var.enable_platform ? [google_compute_managed_ssl_certificate.platform[0].id] : []
  )
}

resource "google_compute_target_https_proxy" "main" {
  name             = "${var.environment}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.main.id
  ssl_certificates = local.ssl_certs

  quic_override = "ENABLE"
}

# HTTP Proxy (for redirect)
resource "google_compute_target_http_proxy" "redirect" {
  name    = "${var.environment}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

# count                 = length(local.ssl_certs) > 0 ? 1 : 0
  name                  = "${var.environment}-https-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_address
  ip_protocol           = "TCP"
  port_range            = "443"
  target                = google_compute_target_https_proxy.main[0]
  port_range            = "443"
  target                = google_compute_target_https_proxy.main.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.environment}-http-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_address
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

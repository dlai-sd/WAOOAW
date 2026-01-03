# Health Checks
resource "google_compute_health_check" "api" {
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

# Backend Services
resource "google_compute_backend_service" "api" {
  name        = "${var.environment}-api-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30
  
  load_balancing_scheme = "EXTERNAL_MANAGED"
  
  backend {
    group           = "projects/${var.project_id}/regions/${var.backend_negs.api.region}/networkEndpointGroups/${var.backend_negs.api.name}"
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }
  
  health_checks = [google_compute_health_check.api.id]
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "customer" {
  name        = "${var.environment}-customer-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30
  
  load_balancing_scheme = "EXTERNAL_MANAGED"
  
  backend {
    group           = "projects/${var.project_id}/regions/${var.backend_negs.customer.region}/networkEndpointGroups/${var.backend_negs.customer.name}"
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }
  
  health_checks = [google_compute_health_check.customer.id]
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_backend_service" "platform" {
  name        = "${var.environment}-platform-backend"
  project     = var.project_id
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 30
  
  load_balancing_scheme = "EXTERNAL_MANAGED"
  
  backend {
    group           = "projects/${var.project_id}/regions/${var.backend_negs.platform.region}/networkEndpointGroups/${var.backend_negs.platform.name}"
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }
  
  health_checks = [google_compute_health_check.platform.id]
  
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# URL Map with multi-domain routing
resource "google_compute_url_map" "main" {
  name            = "${var.environment}-url-map"
  project         = var.project_id
  default_service = google_compute_backend_service.customer.id
  
  host_rule {
    hosts        = [var.customer_domain]
    path_matcher = "customer-matcher"
  }
  
  host_rule {
    hosts        = [var.platform_domain]
    path_matcher = "platform-matcher"
  }
  
  path_matcher {
    name            = "customer-matcher"
    default_service = google_compute_backend_service.customer.id
    
    path_rule {
      paths   = ["/api/*", "/auth/*", "/health"]
      service = google_compute_backend_service.api.id
    }
  }
  
  path_matcher {
    name            = "platform-matcher"
    default_service = google_compute_backend_service.platform.id
    
    path_rule {
      paths   = ["/api/*", "/auth/*", "/health"]
      service = google_compute_backend_service.api.id
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

# SSL Certificates (Google-managed)
resource "google_compute_managed_ssl_certificate" "customer" {
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
  name    = "${var.environment}-platform-ssl"
  project = var.project_id
  
  managed {
    domains = [var.platform_domain]
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# HTTPS Proxy
resource "google_compute_target_https_proxy" "main" {
  name    = "${var.environment}-https-proxy"
  project = var.project_id
  url_map = google_compute_url_map.main.id
  
  ssl_certificates = [
    google_compute_managed_ssl_certificate.customer.id,
    google_compute_managed_ssl_certificate.platform.id
  ]
  
  quic_override = "ENABLE"
}

# HTTP Proxy (for redirect)
resource "google_compute_target_http_proxy" "redirect" {
  name    = "${var.environment}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.http_redirect.id
}

# Forwarding Rules
resource "google_compute_global_forwarding_rule" "https" {
  name                  = "${var.environment}-https-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_name
  ip_protocol           = "TCP"
  port_range            = "443"
  target                = google_compute_target_https_proxy.main.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.environment}-http-forwarding-rule"
  project               = var.project_id
  ip_address            = var.static_ip_name
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

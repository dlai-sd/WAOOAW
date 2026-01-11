environment           = "uat"
project_id            = "waooaw-oauth"
region                = "asia-south1"
static_ip_name        = "waooaw-lb-ip"
enable_backend_api     = true
enable_customer_portal = true
enable_platform_portal = true
backend_image         = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest"
customer_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/customer-portal-v2:latest"
platform_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-v2:latest"
domains = {
  uat = {
    customer_portal = "cp.uat.waooaw.com",
    platform_portal = "pp.uat.waooaw.com",
  }
}
scaling = {
  uat = { min = 1, max = 10 }
}

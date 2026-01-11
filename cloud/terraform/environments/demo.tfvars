environment            = "demo"
project_id             = "waooaw-oauth"
region                 = "asia-south1"
static_ip_name         = "waooaw-lb-ip"
enable_backend_api = true
enable_customer_portal = true
enable_platform_portal = false
backend_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:test-123"
customer_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:test-123"
platform_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:test-pp-456"
domains = {
  demo = {
    customer_portal = "cp.demo.waooaw.com",
    platform_portal = "pp.demo.waooaw.com",
  }
}
scaling = {
  demo = { min = 0, max = 5 }
}

environment           = "demo"
project_id            = "waooaw-oauth"
region                = "asia-south1"
static_ip_name        = "waooaw-lb-ip"
enable_backend_api     = true
enable_customer_portal = true
enable_platform_portal = true
backend_image         = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:demo"
customer_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:demo"
platform_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:demo"
domains = {
  demo = {
    customer_portal = "cp.demo.waooaw.com",
    platform_portal = "pp.demo.waooaw.com",
  }
}
scaling = {
  demo = { min = 0, max = 5 }
}

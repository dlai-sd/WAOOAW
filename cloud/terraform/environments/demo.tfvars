environment           = "demo"
project_id            = "waooaw-oauth"
region                = "asia-south1"
static_ip_name        = "waooaw-lb-ip"
backend_image         = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/backend-v2:latest"
customer_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/customer-portal-v2:latest"
platform_portal_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-v2:latest"
domains = {
  demo = {
    customer_portal = "cp.demo.waooaw.com",
    platform_portal = "pp.demo.waooaw.com",
  }
}
scaling = {
  demo = { min = 0, max = 5 }
}

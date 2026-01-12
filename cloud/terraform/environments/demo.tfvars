environment    = "demo"
project_id     = "waooaw-oauth"
region         = "asia-south1"
static_ip_name = "waooaw-lb-ip"

# Component Enable Flags
enable_cp    = true
enable_pp    = false
enable_plant = false

# Image Variables
cp_frontend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:test-123"
cp_backend_image     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:test-123"
pp_frontend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:test-pp-456"
pp_backend_image     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:test-pp-backend-456"
plant_backend_image  = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:latest"

domains = {
  demo = {
    cp    = "cp.demo.waooaw.com"
    pp    = "pp.demo.waooaw.com"
    plant = "plant.demo.waooaw.com"
  }
}

scaling = {
  demo = { min = 0, max = 5 }
}

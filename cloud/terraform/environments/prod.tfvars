environment    = "prod"
project_id     = "waooaw-oauth"
region         = "asia-south1"
static_ip_name = "waooaw-lb-ip"

# Component Enable Flags
enable_cp    = true
enable_pp    = false
enable_plant = false

# Image Variables
cp_frontend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:prod-latest"
cp_backend_image     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:prod-latest"
pp_frontend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:prod-latest"
pp_backend_image     = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:prod-latest"
plant_backend_image  = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:prod-latest"

domains = {
  prod = {
    cp    = "www.waooaw.com"
    pp    = "pp.waooaw.com"
    plant = "plant.waooaw.com"
  }
}

scaling = {
  prod = { min = 2, max = 100 }
}

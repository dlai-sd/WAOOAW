environment    = "uat"
project_id     = "waooaw-oauth"
region         = "asia-south1"
static_ip_name = "waooaw-lb-ip"

# Component Enable Flags
enable_cp    = true
enable_pp    = false
enable_plant = false

# Image Variables
cp_frontend_image   = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:uat-latest"
cp_backend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:uat-latest"
pp_frontend_image   = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:uat-latest"
pp_backend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:uat-latest"
plant_backend_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:uat-latest"

domains = {
  uat = {
    cp    = "cp.uat.waooaw.com"
    pp    = "pp.uat.waooaw.com"
    plant = "plant.uat.waooaw.com"
  }
}

scaling = {
  uat = { min = 1, max = 10 }
}

project_id     = "waooaw-oauth"
region         = "asia-south1"
static_ip_name = "waooaw-lb-ip"

# Toggle-on when PP/Plant stacks exist and are ready to route.
enable_cp    = true
enable_pp    = true
enable_plant = true

# Bootstrap with demo-only first. Add uat/prod once their app stacks have been applied.
enabled_environments = ["demo"]

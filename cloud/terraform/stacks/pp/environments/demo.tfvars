project_id            = "waooaw-oauth"
region                = "asia-south1"
environment           = "demo"
min_instances         = 0
max_instances         = 5
enable_db_updates     = "true"
allowed_email_domains = "dlaisd.com,waooaw.com,gmail.com,googlemail.com"
enable_dev_token      = "true"
enable_metering_debug = "false"

# VPC Serverless Connector — gives PP backend access to Memorystore Redis (DB /2)
private_network_id = "projects/waooaw-oauth/global/networks/default"
# vpc_connector_cidr uses default 10.8.0.32/28 (Plant=10.8.0.0/28, CP=10.8.0.16/28)

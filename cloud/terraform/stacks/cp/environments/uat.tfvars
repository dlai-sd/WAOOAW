project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "uat"
min_instances = 1
max_instances = 10

# CP OTP settings (capability flags)
otp_delivery_mode        = "provider"
cp_otp_delivery_provider = "smtp"

# Payment mode: 'razorpay' shows both Razorpay + coupon options in BookingModal
payments_mode = "razorpay"

# VPC Serverless Connector — gives CP backend access to Memorystore Redis (DB /3)
private_network_id = "projects/waooaw-oauth/global/networks/default"
# vpc_connector_cidr uses default 10.8.0.16/28 (Plant=10.8.0.0/28, PP=10.8.0.32/28)

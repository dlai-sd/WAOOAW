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

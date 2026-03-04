project_id    = "waooaw-oauth"
region        = "asia-south1"
environment   = "demo"
min_instances = 0
max_instances = 5

# CP OTP settings (capability flags)
otp_delivery_mode        = "provider"
cp_otp_delivery_provider = "smtp"

# Payment mode: 'razorpay' shows both Razorpay + coupon options in BookingModal
payments_mode = "razorpay"

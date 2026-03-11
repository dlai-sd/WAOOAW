from services.cp_otp_delivery import _sender_header


def test_sender_header_adds_waooaw_display_name_when_missing():
    assert _sender_header("customersupport@dlaisd.com") == "WAOOAW Customer Support <customersupport@dlaisd.com>"


def test_sender_header_preserves_existing_display_name():
    sender = "Existing Support <customersupport@dlaisd.com>"
    assert _sender_header(sender) == sender
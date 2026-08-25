"""Webhook signature verification."""

import hashlib
import hmac


def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 over the raw body.

    Baseline uses a plain == comparison (deliberately weak); T04 hardens it
    with app.utils.constant_time_equal.
    """
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return signature == expected

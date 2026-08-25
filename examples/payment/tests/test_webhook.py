import hashlib
import hmac

from app.webhook import verify_signature

SECRET = "s3cret-secret"


def _sig(body: bytes) -> str:
    return hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_verify_signature_valid():
    body = b'{"event": "charge.succeeded"}'
    assert verify_signature(body, _sig(body), SECRET) is True


def test_verify_signature_invalid():
    body = b'{"event": "charge.succeeded"}'
    assert verify_signature(body, "0" * 64, SECRET) is False

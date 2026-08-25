"""Deterministic behavior check for T05 (currency validation).

Run: python spec/t05_currency_check.py     (exit 0 = pass, 1 = fail)

Not collected by pytest (it is not under tests/), so the baseline stays green.
The coder cannot bypass this by writing its own tests — it must make pay()
behave correctly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.payment import PaymentService


class DummyProvider:
    def charge(self, card_token: str, amount_cents: int):
        return True, None


def main() -> int:
    service = PaymentService(DummyProvider())

    # 1. valid currencies succeed
    assert service.pay("tok_1", 100, "CNY").ok, "CNY should succeed"
    assert service.pay("tok_1", 100, "USD").ok, "USD should succeed"

    # 2. unsupported currency raises
    try:
        service.pay("tok_1", 100, "EUR")
    except ValueError as exc:
        assert "unsupported currency" in str(exc), f"wrong message: {exc}"
    else:
        raise SystemExit("FAIL: EUR did not raise ValueError")

    # 3. default currency is CNY
    assert service.pay("tok_1", 100).ok, "default currency should succeed"

    print("t05 currency check: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"t05 currency check: FAIL — {exc}")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"t05 currency check: FAIL — {type(exc).__name__}: {exc}")
        sys.exit(1)

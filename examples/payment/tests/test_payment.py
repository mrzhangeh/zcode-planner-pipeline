from app.payment import PaymentResult, PaymentService


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def charge(self, card_token: str, amount_cents: int):
        self.calls.append((card_token, amount_cents))
        return True, None


def test_pay_success():
    provider = FakeProvider()
    result = PaymentService(provider).pay("tok_1", 5000)
    assert result.ok is True
    assert result.transaction_id
    assert provider.calls == [("tok_1", 5000)]


def test_pay_provider_rejection_returns_error():
    class RejectingProvider:
        def charge(self, card_token, amount_cents):
            return False, "card declined"

    result = PaymentService(RejectingProvider()).pay("tok_2", 5000)
    assert result.ok is False
    assert result.error == "card declined"

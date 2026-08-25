"""Payment domain logic."""

from dataclasses import dataclass
from typing import Optional, Protocol


class PaymentProvider(Protocol):
    """Real providers implement charge(); tests fake it."""

    def charge(self, card_token: str, amount_cents: int) -> tuple[bool, Optional[str]]:
        """Return (ok, error_message)."""
        ...


@dataclass
class PaymentResult:
    ok: bool
    transaction_id: Optional[str] = None
    error: Optional[str] = None
    amount_cents: int = 0


class PaymentService:
    def __init__(self, provider: PaymentProvider) -> None:
        self._provider = provider

    def pay(self, card_token: str, amount_cents: int) -> PaymentResult:
        """Charge a card.

        Baseline behaviour (deliberately incomplete): empty token returns an
        error result instead of raising; amount_cents is not validated.
        """
        if not card_token:
            return PaymentResult(ok=False, error="empty card token", amount_cents=amount_cents)
        ok, err = self._provider.charge(card_token, amount_cents)
        if not ok:
            return PaymentResult(ok=False, error=err, amount_cents=amount_cents)
        return PaymentResult(ok=True, transaction_id="txn-1", amount_cents=amount_cents)

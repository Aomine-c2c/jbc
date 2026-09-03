import random


class MockSMSProvider:
    """Mock SMS provider that returns True by default, with optional simulated failure rate."""

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def send_sms(self, phone: str, message: str) -> bool:
        """Simulate sending an SMS. Returns True on success."""
        if not phone or not message:
            return False
        if self.failure_rate > 0.0:
            return random.random() > self.failure_rate
        return True


_provider_instance: MockSMSProvider | None = None


def get_sms_provider() -> MockSMSProvider:
    """Return the (singleton) SMS provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = MockSMSProvider()
    return _provider_instance

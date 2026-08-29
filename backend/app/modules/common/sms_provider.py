import random


class MockSMSProvider:
    """Mock SMS provider that returns True most of the time."""

    def send_sms(self, phone: str, message: str) -> bool:
        """Simulate sending an SMS. Returns True on success."""
        if not phone or not message:
            return False
        # ~90% success rate
        return random.random() > 0.1


_provider_instance: MockSMSProvider | None = None


def get_sms_provider() -> MockSMSProvider:
    """Return the (singleton) SMS provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = MockSMSProvider()
    return _provider_instance

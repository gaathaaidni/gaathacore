class PaymentProvider:
    """Abstract payment provider interface.

    Concrete providers should implement create_payment_intent, capture, refund, and webhook verification.
    """
    def create_payment_intent(self, amount, currency, metadata=None):
        raise NotImplementedError()

    def capture(self, intent_id):
        raise NotImplementedError()

    def refund(self, payment_id, amount=None):
        raise NotImplementedError()

    def verify_webhook(self, headers, payload):
        raise NotImplementedError()


# Example stub provider that does nothing but demonstrates the contract
class StubProvider(PaymentProvider):
    def create_payment_intent(self, amount, currency, metadata=None):
        return {'id': f'stub_{int(amount*100)}', 'amount': amount, 'currency': currency, 'status': 'created'}

    def capture(self, intent_id):
        return {'id': intent_id, 'status': 'captured'}

    def refund(self, payment_id, amount=None):
        return {'id': payment_id, 'status': 'refunded', 'amount': amount}

    def verify_webhook(self, headers, payload):
        return True

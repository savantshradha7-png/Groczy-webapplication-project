"""Explicitly disabled payment provider interface for the demonstration."""
class PaymentProvider:
    name = "disabled"
    enabled = False

    def create_payment(self, amount, order_reference):
        raise RuntimeError("Online payment is currently disabled in this demonstration project. No money will be charged.")

    def verify_payment(self, payload):
        return False

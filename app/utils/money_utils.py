from decimal import Decimal, ROUND_HALF_UP


def format_currency(amount):
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"₦{amount:,.2f}"

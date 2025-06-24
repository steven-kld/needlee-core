from entities import (
    init_organization_billing,
    get_balance,
    deduct_balance,
    add_payment
)

add_payment(12, 66.8724, "stripe", "paid with debit card")
b, s = get_balance(12)
print(b, s)
from entities import (
    init_organization_billing,
    get_balance,
    deduct_balance,
    add_payment,
    detect_language,
    
)
from atoms import init_openai
# add_payment(12, 66.8724, "stripe", "paid with debit card")
# b, s = get_balance(12)
# print(b, s)

# deduct_balance(12, 10)
# b, s = get_balance(12)
# print(b, s)

openai_client = init_openai()
l = detect_language("напиши вопросы для руководителя компании", openai_client)
print(l)
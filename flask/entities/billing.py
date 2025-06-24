import os
from atoms import run_query
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

PRICE_MAP = {
    "default": Decimal(os.getenv("PRICE_DEFAULT", "0.085")),
    "voice_only": Decimal(os.getenv("PRICE_VOICE_ONLY", "0.050")),
}

def init_organization_billing(org_id: int):
    run_query(
        """
        INSERT INTO billing_accounts (org_id, cash_balance)
        VALUES (%s, %s)
        ON CONFLICT (org_id) DO NOTHING
        """,
        (org_id, 50.00)
    )

def get_balance(org_id: int):
    row = run_query(
        "SELECT cash_balance FROM billing_accounts WHERE org_id = %s FOR UPDATE",
        (org_id,),
        fetch_one=True
    )
    if not row:
        raise ValueError(f"Organization {org_id} not found")
    
    balance = Decimal(row["cash_balance"])
    suspended = balance < Decimal("-2.00")
    return balance, suspended


def deduct_balance(org_id: int, minutes: Decimal, voice_only=False): #
    if not isinstance(minutes, Decimal):
        minutes = Decimal(minutes)

    price_per_minute = PRICE_MAP["voice_only"] if voice_only else PRICE_MAP["default"]
    amount = round(price_per_minute * minutes, 4)
    amount = f"{amount:.6f}"

    run_query(
        """
        UPDATE billing_accounts
        SET cash_balance = cash_balance - %s,
            last_billed_at = NOW()
        WHERE org_id = %s
        """,
        (amount, org_id)
    )

    return amount

def add_payment(org_id: int, amount, method: str = "manual", reference: str = ""):
    amount = Decimal(amount)
    if amount == 0:
        raise ValueError("Payment amount cannot be zero")
    
    # Increase balance
    run_query(
        """
        UPDATE billing_accounts
        SET cash_balance = cash_balance + %s
        WHERE org_id = %s
        """,
        (amount, org_id)
    )

    # Log payment
    run_query(
        """
        INSERT INTO organization_payments (org_id, amount, method, reference)
        VALUES (%s, %s, %s, %s)
        """,
        (org_id, amount, method, reference)
    )

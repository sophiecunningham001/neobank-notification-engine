import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Account, AuditEvent, Card, FraudAlert, PaymentAuthorization, Transfer, User, LedgerEntry
from app.security import hash_password


def seed_database():
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == "sandbox@example.test"))
        if existing:
            return

        user = User(
            email="sandbox@example.test",
            password_hash=hash_password("ChangeMe123!"),
            full_name="Sandbox Customer",
            role="customer",
            is_active=True,
        )
        db.add(user)
        db.flush()

        checking = Account(
            user_id=user.id,
            account_number="2374810001",
            name="Checking",
            account_type="checking",
            balance_cents=482500,
            status="active",
        )
        savings = Account(
            user_id=user.id,
            account_number="2374810002",
            name="High Yield Savings",
            account_type="savings",
            balance_cents=544250,
            status="active",
        )
        db.add_all([checking, savings])
        db.flush()

        db.add_all([
            Card(user_id=user.id, last4="1111", brand="Visa", pan="4111111111111111", status="active"),
            Card(user_id=user.id, last4="0002", brand="Visa", pan="4000000000000002", status="active"),
            Card(user_id=user.id, last4="9995", brand="Visa", pan="4000000000009995", status="active"),
            Card(user_id=user.id, last4="0259", brand="Visa", pan="4000000000000259", status="active"),
        ])

        db.add_all([
            LedgerEntry(account_id=checking.id, entry_type="credit", amount_cents=482500, description="Opening balance"),
            LedgerEntry(account_id=savings.id, entry_type="credit", amount_cents=544250, description="Opening balance"),
        ])

        db.add_all([
            FraudAlert(user_id=user.id, level="low", message="No unusual activity detected."),
            AuditEvent(user_id=user.id, event_type="login", details="Sandbox user authenticated successfully"),
            AuditEvent(user_id=user.id, event_type="account.opened", details="Primary checking account created"),
        ])

        db.commit()
    finally:
        db.close()

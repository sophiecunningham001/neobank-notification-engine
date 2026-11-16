from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import JournalEntry


def account_balance(db: Session, ledger_account_id: str) -> Decimal:
    credits = db.scalar(select(func.coalesce(func.sum(JournalEntry.credit), 0)).where(
        JournalEntry.ledger_account_id == ledger_account_id
    )) or Decimal("0")
    debits = db.scalar(select(func.coalesce(func.sum(JournalEntry.debit), 0)).where(
        JournalEntry.ledger_account_id == ledger_account_id
    )) or Decimal("0")
    return Decimal(str(credits)) - Decimal(str(debits))


def assert_balanced(lines):
    debit_total = sum((Decimal(str(x["debit"])) for x in lines), Decimal("0"))
    credit_total = sum((Decimal(str(x["credit"])) for x in lines), Decimal("0"))
    if debit_total != credit_total:
        raise ValueError("Unbalanced journal")

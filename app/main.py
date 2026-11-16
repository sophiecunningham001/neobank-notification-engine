import secrets
from decimal import Decimal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.dependencies import current_customer
from app.ledger import account_balance, assert_balanced
from app.models import (
    AuditEvent,
    BankAccount,
    Customer,
    JournalEntry,
    JournalTransaction,
    LedgerAccount,
    TransferRequest,
)
from app.schemas import (
    AccountOut,
    CustomerOut,
    LoginIn,
    RegisterIn,
    TokenOut,
    TransferIn,
    TransferOut,
)
from app.security import create_access_token, hash_password, verify_password

app = FastAPI(title=settings.app_name, version="0.1.0", description="Neon Bank sponsor-bank sandbox starter")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


@app.on_event("startup")
def startup():
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def health():
    return {"status": "ok", "environment": settings.app_env, "sandbox_mode": settings.sandbox_mode}


@app.post("/auth/register", response_model=CustomerOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(Customer).where(Customer.email == email)):
        raise HTTPException(409, "Email already registered")
    customer = Customer(email=email, full_name=body.full_name.strip(), password_hash=hash_password(body.password))
    db.add(customer)
    db.flush()
    account = BankAccount(
        owner_id=customer.id,
        account_number=secrets.token_hex(5).upper(),
        account_type="checking",
        currency="USD",
        status="sandbox",
    )
    db.add(account)
    db.flush()
    db.add(LedgerAccount(bank_account_id=account.id, currency="USD"))
    db.add(
        AuditEvent(
            actor_id=customer.id,
            event_type="customer.registered",
            target_id=customer.id,
            details="Sandbox registration; no real deposit account opened",
        )
    )
    db.commit()
    db.refresh(customer)
    return customer


@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    customer = db.scalar(select(Customer).where(Customer.email == body.email.lower()))
    if not customer or not verify_password(body.password, customer.password_hash) or not customer.is_active:
        raise HTTPException(401, "Invalid email or password")
    return TokenOut(access_token=create_access_token(customer.id))


@app.get("/me", response_model=CustomerOut)
def me(customer: Customer = Depends(current_customer)):
    return customer


@app.get("/accounts", response_model=list[AccountOut])
def accounts(db: Session = Depends(get_db), customer: Customer = Depends(current_customer)):
    return list(db.scalars(select(BankAccount).where(BankAccount.owner_id == customer.id)).all())


@app.get("/accounts/{account_id}/balance")
def balance(account_id: str, db: Session = Depends(get_db), customer: Customer = Depends(current_customer)):
    account = db.scalar(select(BankAccount).where(BankAccount.id == account_id, BankAccount.owner_id == customer.id))
    if not account:
        raise HTTPException(404, "Account not found")
    ledger = db.scalar(select(LedgerAccount).where(LedgerAccount.bank_account_id == account.id))
    if ledger is None:
        raise HTTPException(404, "Ledger account not found")
    amount = account_balance(db, ledger.id)
    return {
        "account_id": account.id,
        "ledger_balance": str(amount),
        "available_balance": str(amount),
        "currency": account.currency,
        "status": account.status,
    }


@app.post("/transfers/internal", response_model=TransferOut, status_code=201)
def internal_transfer(
    body: TransferIn,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=12, max_length=128),
    db: Session = Depends(get_db),
    customer: Customer = Depends(current_customer),
):
    if not settings.sandbox_mode:
        raise HTTPException(403, "Live transfers are disabled in this starter")

    prior = db.scalar(select(TransferRequest).where(TransferRequest.idempotency_key == idempotency_key))
    if prior:
        if (
            prior.sender_account_id != body.sender_account_id
            or prior.recipient_account_id != body.recipient_account_id
            or Decimal(str(prior.amount)) != body.amount
        ):
            raise HTTPException(409, "Idempotency key was already used for a different request")
        return prior

    sender = db.scalar(select(BankAccount).where(BankAccount.id == body.sender_account_id, BankAccount.owner_id == customer.id))
    recipient = db.get(BankAccount, body.recipient_account_id)
    if not sender or not recipient:
        raise HTTPException(404, "Sender or recipient account not found")
    if sender.id == recipient.id:
        raise HTTPException(400, "Cannot transfer to the same account")
    if sender.currency != body.currency or recipient.currency != body.currency:
        raise HTTPException(400, "Currency mismatch")
    if sender.status != "sandbox" or recipient.status != "sandbox":
        raise HTTPException(403, "Only sandbox accounts are supported")
    sender_ledger = db.scalar(select(LedgerAccount).where(LedgerAccount.bank_account_id == sender.id))
    recipient_ledger = db.scalar(select(LedgerAccount).where(LedgerAccount.bank_account_id == recipient.id))
    if account_balance(db, sender_ledger.id) < body.amount:
        raise HTTPException(400, "Insufficient sandbox ledger balance")

    journal_id = str(uuid4())
    lines = [
        {"debit": body.amount, "credit": Decimal("0.00")},
        {"debit": Decimal("0.00"), "credit": body.amount},
    ]
    assert_balanced(lines)
    try:
        journal = JournalTransaction(
            id=journal_id,
            transaction_type="internal_transfer",
            idempotency_key=idempotency_key,
            description="Sandbox member transfer",
        )
        db.add(journal)
        db.flush()
        db.add_all(
            [
                JournalEntry(
                    transaction_id=journal.id,
                    ledger_account_id=sender_ledger.id,
                    debit=body.amount,
                    credit=Decimal("0.00"),
                ),
                JournalEntry(
                    transaction_id=journal.id,
                    ledger_account_id=recipient_ledger.id,
                    debit=Decimal("0.00"),
                    credit=body.amount,
                ),
            ]
        )
        transfer = TransferRequest(
            id=str(uuid4()),
            idempotency_key=idempotency_key,
            sender_account_id=sender.id,
            recipient_account_id=recipient.id,
            amount=body.amount,
            currency=body.currency,
            journal_transaction_id=journal.id,
            status="posted",
        )
        db.add(transfer)
        db.add(
            AuditEvent(
                actor_id=customer.id,
                event_type="transfer.internal.posted",
                target_id=transfer.id,
                details=f"Sandbox transfer {body.currency} {body.amount}",
            )
        )
        db.commit()
        db.refresh(transfer)
        return transfer
    except Exception:
        db.rollback()
        raise


@app.get("/transactions")
def transactions(db: Session = Depends(get_db), customer: Customer = Depends(current_customer)):
    account_ids = list(db.scalars(select(BankAccount.id).where(BankAccount.owner_id == customer.id)).all())
    rows = list(
        db.scalars(
            select(TransferRequest)
            .where((TransferRequest.sender_account_id.in_(account_ids)) | (TransferRequest.recipient_account_id.in_(account_ids)))
            .order_by(TransferRequest.created_at.desc())
            .limit(100)
        ).all()
    )
    return [
        {
            "id": r.id,
            "sender_account_id": r.sender_account_id,
            "recipient_account_id": r.recipient_account_id,
            "amount": str(r.amount),
            "currency": r.currency,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]

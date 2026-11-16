from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.models import Account, AuditEvent, Card, FraudAlert, LedgerEntry, PaymentAuthorization, Transfer, User
from app.schemas import (
    AccountResponse,
    CardResponse,
    LoginRequest,
    PaymentRequest,
    PaymentResponse,
    TokenResponse,
    TransferRequest,
    TransferResponse,
    UserResponse,
)
from app.security import create_token, hash_password, verify_password

from main import app


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(user.id))


@app.get("/api/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/accounts", response_model=list[AccountResponse])
def list_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).where(Account.user_id == current_user.id)).all()
    return [
        AccountResponse(
            id=a.id,
            account_number=a.account_number,
            name=a.name,
            account_type=a.account_type,
            balance_cents=a.balance_cents,
            status=a.status,
        )
        for a in accounts
    ]


@app.get("/api/cards", response_model=list[CardResponse])
def list_cards(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cards = db.scalars(select(Card).where(Card.user_id == current_user.id)).all()
    return [
        CardResponse(
            id=c.id,
            last4=c.last4,
            brand=c.brand,
            pan=c.pan,
            status=c.status,
        )
        for c in cards
    ]


@app.post("/api/payments/authorize", response_model=PaymentResponse)
def authorize_payment(payload: PaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.scalar(select(Card).where(Card.pan == payload.pan, Card.user_id == current_user.id))
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

    if payload.amount_cents > 150000:
        status_value = "declined"
    elif payload.pan.endswith("0259"):
        status_value = "fraud_blocked"
    elif payload.pan.endswith("9995"):
        status_value = "insufficient_funds"
    elif payload.pan.endswith("0002"):
        status_value = "declined"
    else:
        status_value = "approved"

    record = PaymentAuthorization(
        user_id=current_user.id,
        card_pan=payload.pan,
        amount_cents=payload.amount_cents,
        merchant=payload.merchant,
        status=status_value,
        idempotency_key=payload.idempotency_key,
    )
    db.add(record)
    db.add(
        AuditEvent(
            user_id=current_user.id,
            event_type="payment.authorized",
            details=f"Merchant: {payload.merchant}; status: {status_value}; amount_cents: {payload.amount_cents}",
        )
    )
    db.commit()
    return PaymentResponse(id=record.id, status=status_value, amount_cents=payload.amount_cents, merchant=payload.merchant)


@app.get("/api/payments/history")
def payment_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(PaymentAuthorization).where(PaymentAuthorization.user_id == current_user.id).order_by(PaymentAuthorization.created_at.desc())).all()
    return [{
        "id": row.id,
        "merchant": row.merchant,
        "amount_cents": row.amount_cents,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@app.post("/api/transfers", response_model=TransferResponse)
def create_transfer(payload: TransferRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account")

    from_account = db.get(Account, payload.from_account_id)
    to_account = db.get(Account, payload.to_account_id)
    if not from_account or not to_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if from_account.user_id != current_user.id or to_account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account does not belong to the user")

    if from_account.balance_cents < payload.amount_cents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    transfer = Transfer(
        user_id=current_user.id,
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount_cents=payload.amount_cents,
        status="posted",
        idempotency_key=payload.idempotency_key,
    )
    db.add(transfer)
    db.add(LedgerEntry(account_id=payload.from_account_id, entry_type="debit", amount_cents=payload.amount_cents, description="Internal transfer out"))
    db.add(LedgerEntry(account_id=payload.to_account_id, entry_type="credit", amount_cents=payload.amount_cents, description="Internal transfer in"))
    from_account.balance_cents -= payload.amount_cents
    to_account.balance_cents += payload.amount_cents
    db.add(AuditEvent(user_id=current_user.id, event_type="transfer.posted", details=f"Transfer of {payload.amount_cents} cents posted"))
    db.commit()
    return TransferResponse(id=transfer.id, status=transfer.status, amount_cents=payload.amount_cents)


@app.get("/api/ledger/entries")
def ledger_entries(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(LedgerEntry).where(LedgerEntry.account_id.in_([a.id for a in db.scalars(select(Account).where(Account.user_id == current_user.id)).all()])).order_by(LedgerEntry.created_at.desc())).all()
    return [{
        "id": row.id,
        "account_id": row.account_id,
        "entry_type": row.entry_type,
        "amount_cents": row.amount_cents,
        "description": row.description,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@app.get("/api/ledger/gl-accounts")
def gl_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).where(Account.user_id == current_user.id)).all()
    return [{
        "account_id": account.id,
        "account_name": account.name,
        "balance_cents": account.balance_cents,
    } for account in accounts]


@app.get("/api/fraud/posture")
def fraud_posture(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alerts = db.scalars(select(FraudAlert).where(FraudAlert.user_id == current_user.id)).all()
    return {
        "score": 14,
        "status": "low_risk",
        "alerts": len(alerts),
        "summary": "No recent anomalies detected.",
    }


@app.get("/api/fraud/alerts")
def fraud_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alerts = db.scalars(select(FraudAlert).where(FraudAlert.user_id == current_user.id).order_by(FraudAlert.created_at.desc())).all()
    return [{
        "id": a.id,
        "level": a.level,
        "message": a.message,
        "created_at": a.created_at.isoformat(),
    } for a in alerts]


@app.get("/api/audit/events")
def audit_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditEvent).where(AuditEvent.user_id == current_user.id).order_by(AuditEvent.created_at.desc()).limit(20)).all()
    return [{
        "id": row.id,
        "event_type": row.event_type,
        "details": row.details,
        "created_at": row.created_at.isoformat(),
    } for row in rows]


@app.post("/api/test/simulate-error")
def simulate_error():
    raise HTTPException(status_code=500, detail={"code": "SIMULATED_ERROR", "message": "This is a demo error envelope generated by the sandbox."})


@app.get("/health")
def health():
    return {"status": "ok", "message": "Neon Bank sandbox is healthy"}

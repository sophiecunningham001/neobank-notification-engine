from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class AccountResponse(BaseModel):
    id: str
    account_number: str
    name: str
    account_type: str
    balance_cents: int
    status: str
    model_config = ConfigDict(from_attributes=True)


class CardResponse(BaseModel):
    id: str
    last4: str
    brand: str
    pan: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class PaymentRequest(BaseModel):
    pan: str
    amount_cents: int = Field(gt=0)
    merchant: str
    idempotency_key: str = Field(min_length=3, max_length=128)


class PaymentResponse(BaseModel):
    id: str
    status: str
    amount_cents: int
    merchant: str
    model_config = ConfigDict(from_attributes=True)


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount_cents: int = Field(gt=0)
    idempotency_key: str = Field(min_length=3, max_length=128)


class TransferResponse(BaseModel):
    id: str
    status: str
    amount_cents: int
    model_config = ConfigDict(from_attributes=True)

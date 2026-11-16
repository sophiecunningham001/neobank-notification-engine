from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CustomerOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    kyc_status: str
    model_config = ConfigDict(from_attributes=True)


class AccountOut(BaseModel):
    id: str
    account_number: str
    account_type: str
    currency: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class TransferIn(BaseModel):
    sender_account_id: str
    recipient_account_id: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class TransferOut(BaseModel):
    id: str
    status: str
    amount: Decimal
    currency: str
    journal_transaction_id: str
    model_config = ConfigDict(from_attributes=True)

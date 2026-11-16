from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=True)


def current_customer(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Session = Depends(get_db),
):
    customer_id = decode_access_token(credentials.credentials)
    customer = db.get(Customer, customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(status_code=401, detail="Customer account unavailable")
    return customer

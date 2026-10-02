from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inquiries.models import Customer, Inquiry
from app.inquiries.schemas import InquiryCreate


class CustomerNotFound(Exception):
    pass


class IdempotencyConflict(Exception):
    pass


def existing_inquiry(session: Session, data: InquiryCreate) -> Inquiry | None:
    inquiry = session.scalar(
        select(Inquiry).where(Inquiry.idempotency_key == data.idempotency_key)
    )
    if inquiry is not None:
        if inquiry.customer_id != data.customer_id or inquiry.body != data.body:
            raise IdempotencyConflict
    return inquiry


def create_inquiry(session: Session, data: InquiryCreate) -> tuple[Inquiry, bool]:
    existing = existing_inquiry(session, data)
    if existing is not None:
        return existing, False
    if session.get(Customer, data.customer_id) is None:
        raise CustomerNotFound

    inquiry = Inquiry(**data.model_dump())
    session.add(inquiry)
    try:
        session.commit()
    except IntegrityError:
        # Another request may have committed the same key during this request.
        session.rollback()
        existing = existing_inquiry(session, data)
        if existing is not None:
            return existing, False
        raise
    session.refresh(inquiry)
    return inquiry, True

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.inquiries.schemas import InquiryCreate, InquiryResponse
from app.inquiries.service import CustomerNotFound, IdempotencyConflict, create_inquiry, get_inquiry

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


@router.post(
    "", response_model=InquiryResponse, status_code=201,
    responses={
        200: {"model": InquiryResponse, "description": "Existing inquiry for an identical request"},
        404: {"description": "Customer not found"},
        409: {"description": "Idempotency key used for a different request"},
    },
)
def post_inquiry(
    data: InquiryCreate,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> InquiryResponse:
    try:
        inquiry, created = create_inquiry(session, data)
    except CustomerNotFound:
        raise HTTPException(status_code=404, detail="Customer not found") from None
    except IdempotencyConflict:
        raise HTTPException(
            status_code=409, detail="Idempotency key already used for a different request"
        ) from None
    if not created:
        response.status_code = 200
    return InquiryResponse.model_validate(inquiry)


@router.get("/{inquiry_id}", response_model=InquiryResponse,
            responses={404: {"description": "Inquiry not found"}})
def read_inquiry(
    inquiry_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> InquiryResponse:
    inquiry = get_inquiry(session, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return InquiryResponse.model_validate(inquiry)

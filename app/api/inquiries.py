from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.inquiries.schemas import InquiryCreate, InquiryResponse
from app.inquiries.service import CustomerNotFound, IdempotencyConflict, create_inquiry

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

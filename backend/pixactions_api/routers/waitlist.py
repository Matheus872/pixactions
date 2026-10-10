from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..deps import SessionDep
from ..errors import ErrorCode, error_responses
from ..models import WaitlistRow
from ..schemas.waitlist import WaitlistIn, WaitlistOut

router = APIRouter(prefix="/v1", tags=["Waitlist"])


@router.post(
    "/waitlist",
    response_model=WaitlistOut,
    summary="Join the waitlist",
    responses=error_responses(ErrorCode.VALIDATION_ERROR),
)
async def join_waitlist(body: WaitlistIn, session: SessionDep) -> WaitlistOut:
    """Adds an email to the waitlist. The response is identical whether or not the email was already
    on the list, so the endpoint cannot be used to find out who signed up."""
    email = body.email.lower()
    if await session.scalar(select(WaitlistRow).where(WaitlistRow.email == email)) is None:
        session.add(WaitlistRow(email=email, role=body.role, lang=body.lang))
        try:
            await session.commit()
        except IntegrityError:  # concurrent signup of the same email
            await session.rollback()
    return WaitlistOut(received=True)

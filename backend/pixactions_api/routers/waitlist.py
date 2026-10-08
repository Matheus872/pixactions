from fastapi import APIRouter
from sqlalchemy import select

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
    """Adds an email to the waitlist. Idempotent by (case-insensitive) email: repeating the call returns
    `created: false` instead of an error."""
    email = body.email.lower()
    existing = await session.scalar(select(WaitlistRow).where(WaitlistRow.email == email))
    if existing is not None:
        return WaitlistOut(email=email, role=existing.role, created=False)
    session.add(WaitlistRow(email=email, role=body.role, lang=body.lang))
    await session.commit()
    return WaitlistOut(email=email, role=body.role, created=True)

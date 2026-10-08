from fastapi import APIRouter

from .. import __version__
from ..deps import ServiceDep, SettingsDep
from ..schemas.health import HealthOut
from ..solana.constants import PROGRAM_ID

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthOut, summary="Service health")
async def health(settings: SettingsDep, service: ServiceDep) -> HealthOut:
    """Returns the API status plus the Solana cluster, program id, service wallet (fee payer and mock
    on-ramp) and payment mint currently in use."""
    return HealthOut(
        status="ok",
        version=__version__,
        env=settings.env,
        cluster=settings.solana_cluster,
        program_id=str(PROGRAM_ID),
        service_wallet=str(service.pubkey()),
        payment_mint=settings.mock_usdc_mint,
    )

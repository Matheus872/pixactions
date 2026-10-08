from pydantic import BaseModel, ConfigDict


class HealthOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "version": "0.1.0",
                    "env": "production",
                    "cluster": "devnet",
                    "program_id": "PiXAct1ons1111111111111111111111111111111111",
                    "service_wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    "payment_mint": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
                }
            ]
        }
    )

    status: str
    version: str
    env: str
    cluster: str
    program_id: str
    service_wallet: str
    payment_mint: str

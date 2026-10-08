from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ActionRule(BaseModel):
    pathPattern: str
    apiPath: str


class ActionsJson(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"rules": [{"pathPattern": "/actions/**", "apiPath": "/actions/**"}]}]})

    rules: list[ActionRule]


class ActionError(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"message": "Event is sold out"}]})

    message: str


class ActionLink(BaseModel):
    type: Literal["transaction"] = "transaction"
    label: str
    href: str


class ActionLinks(BaseModel):
    actions: list[ActionLink]


class ActionGetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "action",
                    "icon": "https://pixactions.app/opengraph-image",
                    "title": "Meetup Solana SP",
                    "description": "São Paulo, SP · 20/10/2026 22:00 UTC · R$ 20.00",
                    "label": "Comprar ingresso · 3.64 USDC",
                    "disabled": False,
                    "links": {"actions": [{"type": "transaction", "label": "Comprar ingresso · 3.64 USDC", "href": "/actions/events/meetup-solana-sp-3f9a"}]},
                    "error": None,
                }
            ]
        }
    )

    type: Literal["action"] = "action"
    icon: str
    title: str
    description: str
    label: str
    disabled: bool = False
    links: ActionLinks | None = None
    error: ActionError | None = None


class ActionPostRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"account": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"}]})

    account: str = Field(description="Wallet that will sign and own the ticket.")


class ActionPostResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"type": "transaction", "transaction": "AgAAAA...==", "message": "Ingresso emitido na Solana!"}]})

    type: Literal["transaction"] = "transaction"
    transaction: str = Field(description="Base64 tx, already signed by the API as fee payer.")
    message: str | None = None

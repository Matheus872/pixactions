from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["organizer", "buyer", "developer"]


class WaitlistIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "ana@example.com", "role": "organizer", "lang": "pt"}]})

    email: EmailStr
    role: Role = Field(description="Who is signing up.")
    lang: Literal["pt", "en"] = "pt"


class WaitlistOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"received": True}]})

    received: bool = Field(description="Always true: the answer is the same for new and existing emails.")

from typing import Optional
from pydantic import BaseModel, Field


class WahaMediaPayload(BaseModel):
    url: Optional[str] = None
    mimetype: Optional[str] = None


class WahaInnerData(BaseModel):
    notifyName: Optional[str] = None


class WahaMessagePayload(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    from_field: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    body: Optional[str] = None
    fromMe: bool = False
    hasMedia: bool = False
    media: Optional[WahaMediaPayload] = None
    inner_data: Optional[WahaInnerData] = Field(None, alias="_data")


class WahaWebhookRequest(BaseModel):
    event: Optional[str] = None
    payload: WahaMessagePayload

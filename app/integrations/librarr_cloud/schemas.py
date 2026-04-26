from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.metadata import MetadataResult


class EnrichRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: str  # free-text query e.g. "The Left Hand of Darkness Ursula Le Guin"
    entity_type: str  # "book", "author", or "edition"


class EnrichStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_id: str
    status: Literal["pending", "complete", "failed"]
    result: MetadataResult | None = None  # present when status == "complete"


class LookupResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    result: MetadataResult | None = None  # None when not in cloud cache


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    request_id: str  # the enrich request this feedback applies to
    field: str  # which field was wrong e.g. "title", "author"
    correct_value: str  # what the correct value is
    entity_type: str  # "book", "author", or "edition"

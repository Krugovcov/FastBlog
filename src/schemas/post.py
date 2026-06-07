from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PostSchema(BaseModel):
    title: str = Field(min_length=1)
    content: str
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostUpdateSchema(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostResponse(BaseModel):
    id: int
    user_id: int

    title: str
    content: str
    slug: str
    url: Optional[str]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
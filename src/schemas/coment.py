from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CommentaryResponseSchema(BaseModel):
    id: int
    content: str
    user_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentaryCreateSchema(BaseModel):
    post_id: int
    content: str


class CommentaryUpdateSchema(BaseModel):
    content: str
import uuid
from datetime import datetime

from pydantic import BaseModel


class BulletRewriteSuggestion(BaseModel):
    original: str
    rewritten: str
    rationale: str


class RewriteSuggestionsRead(BaseModel):
    resume_id: uuid.UUID
    suggestions: list[BulletRewriteSuggestion]
    model: str
    generated_at: datetime

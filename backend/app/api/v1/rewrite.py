import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.rewrite import RewriteSuggestionsRead
from app.services.rewrite_suggestions import (
    RewriteNotConfiguredError,
    RewriteProviderError,
    generate_rewrite_suggestions,
)

router = APIRouter(tags=["AI Rewrite"])


@router.post("/resumes/{resume_id}/rewrite-suggestions", response_model=RewriteSuggestionsRead)
def get_rewrite_suggestions(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RewriteSuggestionsRead:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    if not resume.raw_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume has no extracted text to generate suggestions from",
        )

    try:
        return generate_rewrite_suggestions(resume)
    except RewriteNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RewriteProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

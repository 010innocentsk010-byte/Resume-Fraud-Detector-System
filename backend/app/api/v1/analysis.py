import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.analysis import AnalysisRead

router = APIRouter(tags=["Analysis"])


@router.get("/analysis/{analysis_id}", response_model=AnalysisRead)
def get_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisRead:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return AnalysisRead.model_validate(analysis)


@router.get("/resumes/{resume_id}/analysis", response_model=AnalysisRead)
def get_latest_analysis_for_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisRead:
    analysis = db.scalar(
        select(Analysis).where(Analysis.resume_id == resume_id).order_by(Analysis.created_at.desc()).limit(1)
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis found for this resume yet")
    return AnalysisRead.model_validate(analysis)

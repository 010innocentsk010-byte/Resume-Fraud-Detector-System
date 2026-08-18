import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.applicant import Applicant
from app.models.resume import Resume
from app.models.user import User
from app.schemas.applicant import ApplicantCreate, ApplicantRead

router = APIRouter(prefix="/applicants", tags=["Applicants"])


def _latest_analysis_for(db: Session, applicant_id: uuid.UUID) -> Analysis | None:
    return db.scalar(
        select(Analysis)
        .join(Resume, Resume.id == Analysis.resume_id)
        .where(Resume.applicant_id == applicant_id)
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )


def _to_applicant_read(db: Session, applicant: Applicant) -> ApplicantRead:
    resume_count = db.scalar(select(func.count()).select_from(Resume).where(Resume.applicant_id == applicant.id)) or 0
    latest_analysis = _latest_analysis_for(db, applicant.id)
    return ApplicantRead(
        id=applicant.id,
        name=applicant.name,
        email=applicant.email,
        phone=applicant.phone,
        field_of_study=applicant.field_of_study,
        created_at=applicant.created_at,
        resume_count=resume_count,
        latest_resume_id=latest_analysis.resume_id if latest_analysis else None,
        latest_fraud_score=latest_analysis.fraud_score if latest_analysis else None,
        latest_risk_level=latest_analysis.risk_level if latest_analysis else None,
        latest_flag_count=len(latest_analysis.flags) if latest_analysis else None,
    )


@router.post("", response_model=ApplicantRead, status_code=status.HTTP_201_CREATED)
def create_applicant(
    payload: ApplicantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicantRead:
    applicant = Applicant(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        field_of_study=payload.field_of_study,
        created_by_id=current_user.id,
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)
    return _to_applicant_read(db, applicant)


@router.get("", response_model=list[ApplicantRead])
def list_applicants(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApplicantRead]:
    stmt = select(Applicant).order_by(Applicant.created_at.desc())
    if q:
        stmt = stmt.where(Applicant.name.ilike(f"%{q}%") | Applicant.email.ilike(f"%{q}%"))
    applicants = db.scalars(stmt).all()
    return [_to_applicant_read(db, applicant) for applicant in applicants]


@router.get("/{applicant_id}", response_model=ApplicantRead)
def get_applicant(
    applicant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicantRead:
    applicant = db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
    return _to_applicant_read(db, applicant)


@router.delete("/{applicant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_applicant(
    applicant_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    applicant = db.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")

    db.delete(applicant)
    db.commit()

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.job_match import JobMatch
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportRead
from app.services.report_generator import generate_report_pdf

router = APIRouter(tags=["Reports"])


@router.get("/reports/{analysis_id}", response_model=ReportRead)
def get_report(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportRead:
    report = db.query(Report).filter(Report.analysis_id == analysis_id).order_by(Report.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found for this analysis")
    return ReportRead.model_validate(report)


@router.get("/reports/{analysis_id}/pdf")
def download_report_pdf(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    report = db.query(Report).filter(Report.analysis_id == analysis_id).order_by(Report.created_at.desc()).first()
    recommendation = report.recommendation if report else ""

    resume = analysis.resume
    applicant = resume.applicant

    job_match = db.scalar(
        select(JobMatch).where(JobMatch.resume_id == resume.id).order_by(JobMatch.created_at.desc()).limit(1)
    )

    pdf_bytes = generate_report_pdf(analysis, resume, applicant, recommendation, job_match)
    filename = f"fraud-report-{applicant.name.replace(' ', '_')}-{analysis.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

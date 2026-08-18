from fastapi import APIRouter

from app.api.v1 import (
    analysis,
    applicants,
    auth,
    dashboard,
    education,
    job_match,
    job_postings,
    public,
    reports,
    resumes,
    rewrite,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(applicants.router)
api_router.include_router(resumes.router)
api_router.include_router(analysis.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(job_match.router)
api_router.include_router(job_postings.router)
api_router.include_router(public.router)
api_router.include_router(rewrite.router)
api_router.include_router(education.router)

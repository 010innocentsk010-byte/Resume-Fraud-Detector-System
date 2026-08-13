import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.resume import ResumeFileType, ResumeStatus


class ParsedContact(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class ParsedEducationEntry(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    raw_text: str


class ParsedExperienceEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    raw_text: str


class ParsedResume(BaseModel):
    contact: ParsedContact
    skills: list[str] = []
    education: list[ParsedEducationEntry] = []
    experience: list[ParsedExperienceEntry] = []
    certifications: list[str] = []
    projects: list[str] = []
    sections_found: list[str] = []


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_id: uuid.UUID
    original_filename: str
    file_type: ResumeFileType
    file_size_bytes: int
    status: ResumeStatus
    created_at: datetime


class ResumeDetail(ResumeRead):
    parsed_data: ParsedResume | None = None

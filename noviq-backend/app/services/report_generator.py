"""Renders a downloadable PDF fraud report from an Analysis record."""
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.analysis import Analysis, RiskLevel
from app.models.applicant import Applicant
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.services.job_match import build_match_recommendation
from app.services.storage import get_storage

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)

RISK_STYLES = {
    RiskLevel.HIGH: {"risk_color": "#dc2626", "risk_bg": "#fef2f2", "risk_border": "#fecaca"},
    RiskLevel.MEDIUM: {"risk_color": "#d97706", "risk_bg": "#fffbeb", "risk_border": "#fde68a"},
    RiskLevel.LOW: {"risk_color": "#16a34a", "risk_bg": "#f0fdf4", "risk_border": "#bbf7d0"},
}


def render_report_html(
    analysis: Analysis,
    resume: Resume,
    applicant: Applicant,
    recommendation: str,
    job_match: JobMatch | None = None,
) -> str:
    template = _env.get_template("report.html")
    style = RISK_STYLES[analysis.risk_level]
    return template.render(
        applicant_name=applicant.name,
        filename=resume.original_filename,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M GMT"),
        fraud_score=analysis.fraud_score,
        risk_level=analysis.risk_level.value,
        ats_score=analysis.ats_score,
        ai_score=analysis.ai_score,
        scores=analysis,
        recommendation=recommendation,
        flags=analysis.flags,
        job_match=job_match,
        job_match_recommendation=build_match_recommendation(job_match.match_score) if job_match else None,
        **style,
    )


def generate_report_pdf(
    analysis: Analysis,
    resume: Resume,
    applicant: Applicant,
    recommendation: str,
    job_match: JobMatch | None = None,
) -> bytes:
    html_content = render_report_html(analysis, resume, applicant, recommendation, job_match)

    try:
        from weasyprint import HTML
    except OSError:
        # WeasyPrint's native GTK/Pango libraries aren't installed on this host
        # (common on local Windows dev). Fall back to the standalone CLI build.
        return _generate_report_pdf_via_cli(html_content)

    return HTML(string=html_content, base_url=str(TEMPLATE_DIR)).write_pdf()


def _find_standalone_weasyprint_cli() -> str | None:
    # pip also installs a same-named "weasyprint" console-script shim inside the
    # active venv's Scripts/ dir, which just re-imports the same broken Python
    # package and fails for the identical reason. shutil.which() would find that
    # shim first since the venv is prepended to PATH, so check known standalone
    # install locations (e.g. `choco install weasyprint`) before falling back.
    known_paths = [
        Path(r"C:\ProgramData\chocolatey\bin\weasyprint.exe"),
        Path(r"C:\ProgramData\chocolatey\lib\weasyprint\tools\dist\weasyprint.exe"),
    ]
    for path in known_paths:
        if path.is_file():
            return str(path)

    found = shutil.which("weasyprint")
    if found and ".venv" not in Path(found).parts and "venv" not in Path(found).parts:
        return found
    return None


def _generate_report_pdf_via_cli(html_content: str) -> bytes:
    exe = _find_standalone_weasyprint_cli()
    if not exe:
        raise RuntimeError(
            "PDF generation unavailable: WeasyPrint's native libraries are missing and no "
            "standalone 'weasyprint' CLI fallback was found."
        )
    result = subprocess.run(
        [exe, "-u", str(TEMPLATE_DIR), "-", "-"],
        input=html_content.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return result.stdout


def save_report_pdf(analysis: Analysis, resume: Resume, applicant: Applicant, recommendation: str) -> str:
    pdf_bytes = generate_report_pdf(analysis, resume, applicant, recommendation)
    storage = get_storage()
    return storage.save(pdf_bytes, f"report-{analysis.id}.pdf")

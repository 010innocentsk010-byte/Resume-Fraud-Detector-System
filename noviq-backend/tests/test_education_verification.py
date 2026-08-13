import uuid
from types import SimpleNamespace

import httpx
import pytest

from app.core import rate_limit
from app.models.education_verification import VerificationSource, VerificationStatus, VerifiedSchool
from app.services import education_verification as svc


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def __call__(self, *args, **kwargs):
        return self._result


class FakeSession:
    """Stand-in for SQLAlchemy Session: scalar() returns a preset local match,
    add()/commit() just record what was logged."""

    def __init__(self, local_match=None):
        self._local_match = local_match
        self.added = []
        self.committed = False

    def scalar(self, *args, **kwargs):
        return self._local_match

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True


def _fake_httpx_response(status_code: int, json_body: dict | None = None):
    request = httpx.Request("POST", "https://api.ghana.dev/api/v1/education")
    content = None
    if json_body is not None:
        import json

        content = json.dumps(json_body).encode()
    return httpx.Response(status_code, request=request, content=content)


def test_local_match_short_circuits_external_call(monkeypatch):
    local = VerifiedSchool(
        id=uuid.uuid4(), full_name="Kwesi Owusu", school_name="University of Ghana",
        degree="BSc Computer Science", graduation_year=2019,
    )
    db = FakeSession(local_match=local)

    def boom(*args, **kwargs):
        raise AssertionError("External API should not be called when a local match exists")

    monkeypatch.setattr(svc.httpx, "post", boom)

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Kwesi Owusu", school_name="University of Ghana",
        degree="BSc Computer Science", graduation_year=2019, candidate_consent=True,
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.verified_by == VerificationSource.LOCAL_DB
    assert result.details.school == "University of Ghana"
    assert db.committed is True
    assert len(db.added) == 1
    assert db.added[0].status == VerificationStatus.VERIFIED
    assert result.summary == (
        "Kwesi Owusu has been verified to have attended University of Ghana. "
        "Records confirm completion of BSc Computer Science in 2019."
    )


def test_no_local_match_and_no_api_key_returns_pending(monkeypatch):
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "")
    db = FakeSession(local_match=None)

    def boom(*args, **kwargs):
        raise AssertionError("External API should not be called without an API key configured")

    monkeypatch.setattr(svc.httpx, "post", boom)

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Nobody Here", school_name="Unknown University",
        degree="BSc Nothing", graduation_year=2020, candidate_consent=True,
    )

    assert result.status == VerificationStatus.PENDING
    assert result.verified_by is None
    assert "pending" in result.summary.lower()
    assert "Unknown University" in result.summary


def test_external_api_verified_response(monkeypatch):
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "test-key")
    db = FakeSession(local_match=None)

    def fake_post(*args, **kwargs):
        return _fake_httpx_response(200, {"found": True, "school_name": "UCC", "degree": "BEd", "graduation_year": 2019})

    monkeypatch.setattr(svc.httpx, "post", fake_post)

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Efua Sarpong", school_name="University of Cape Coast",
        degree="BEd Mathematics", graduation_year=2019, candidate_consent=True,
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.verified_by == VerificationSource.GHANA_API


def test_external_api_not_found_response(monkeypatch):
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "test-key")
    db = FakeSession(local_match=None)
    monkeypatch.setattr(svc.httpx, "post", lambda *a, **k: _fake_httpx_response(200, {"found": False}))

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Nobody", school_name="Nowhere University",
        degree="BSc Nothing", graduation_year=2020, candidate_consent=True,
    )

    assert result.status == VerificationStatus.NOT_FOUND
    assert result.verified_by == VerificationSource.GHANA_API
    assert "No record was found" in result.summary
    assert "Nobody" in result.summary


def test_summary_never_invents_fields_not_in_the_response(monkeypatch):
    """Regression guard: the summary template must only ever use fields already
    present on the request/response — it must never fabricate a value (e.g. a
    student ID) for data the verification never actually established."""
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "test-key")
    db = FakeSession(local_match=None)
    monkeypatch.setattr(svc.httpx, "post", lambda *a, **k: _fake_httpx_response(200, {"found": False}))

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Nobody", school_name="Nowhere University",
        degree="BSc Nothing", graduation_year=2020, candidate_consent=True,
    )

    assert "student id" not in result.summary.lower()
    assert "id:" not in result.summary.lower()


@pytest.mark.parametrize("status_code", [401, 404, 500])
def test_external_api_error_statuses_handled_gracefully(monkeypatch, status_code):
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "test-key")
    db = FakeSession(local_match=None)
    monkeypatch.setattr(svc.httpx, "post", lambda *a, **k: _fake_httpx_response(status_code))

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Nobody", school_name="Nowhere University",
        degree="BSc Nothing", graduation_year=2020, candidate_consent=True,
    )

    assert result.status in (VerificationStatus.ERROR, VerificationStatus.NOT_FOUND)
    assert result.status != VerificationStatus.VERIFIED


def test_external_api_connection_error_returns_error_status(monkeypatch):
    monkeypatch.setattr(svc.settings, "GHANA_EDU_API_KEY", "test-key")
    db = FakeSession(local_match=None)

    def raise_connect_error(*args, **kwargs):
        raise httpx.ConnectError("boom", request=httpx.Request("POST", "https://api.ghana.dev/api/v1/education"))

    monkeypatch.setattr(svc.httpx, "post", raise_connect_error)

    result = svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Nobody", school_name="Nowhere University",
        degree="BSc Nothing", graduation_year=2020, candidate_consent=True,
    )

    assert result.status == VerificationStatus.ERROR
    assert result.verified_by is None
    assert "system error" in result.summary.lower()


def test_verification_log_records_denied_consent_flag():
    """candidate_consent is persisted on the log row as-is; the router (not the
    service) is what actually blocks the request when consent is False."""
    local = VerifiedSchool(
        id=uuid.uuid4(), full_name="Kwesi Owusu", school_name="University of Ghana",
        degree="BSc Computer Science", graduation_year=2019,
    )
    db = FakeSession(local_match=local)

    svc.verify_education(
        db=db, applicant_id=uuid.uuid4(), requested_by_id=uuid.uuid4(),
        full_name="Kwesi Owusu", school_name="University of Ghana",
        degree="BSc Computer Science", graduation_year=2019, candidate_consent=False,
    )

    assert db.added[0].candidate_consent is False


def test_rate_limiter_allows_up_to_max_then_blocks():
    key = f"test-user-{uuid.uuid4()}"
    for _ in range(3):
        rate_limit.enforce_rate_limit(key, max_calls=3, window_seconds=60)

    with pytest.raises(rate_limit.RateLimitExceededError):
        rate_limit.enforce_rate_limit(key, max_calls=3, window_seconds=60)


def test_rate_limiter_is_scoped_per_key():
    rate_limit.enforce_rate_limit(f"user-a-{uuid.uuid4()}", max_calls=1, window_seconds=60)
    # A different key must not be affected by user-a's usage.
    rate_limit.enforce_rate_limit(f"user-b-{uuid.uuid4()}", max_calls=1, window_seconds=60)

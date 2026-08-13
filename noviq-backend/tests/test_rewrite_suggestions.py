import json
import uuid
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.services import rewrite_suggestions as svc

RESUME_TEXT = """John Doe
john@example.com

Experience
Software Engineer at Acme Corp
Jan 2020 - Present
Responsible for maintaining the backend systems.
Led a team of 5 engineers to deliver a 30% reduction in API latency.
"""


def _fake_resume(raw_text: str = RESUME_TEXT):
    return SimpleNamespace(id=uuid.uuid4(), raw_text=raw_text)


def _fake_response(text: str):
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


def _api_error(cls, message="boom", status_code=500):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code, request=request)
    return cls(message, response=response, body=None)


def test_select_weak_bullets_flags_weak_lines():
    weak = svc.select_weak_bullets(RESUME_TEXT)
    originals = [w["original"] for w in weak]
    assert any("Responsible for maintaining" in o for o in originals)


def test_select_weak_bullets_does_not_flag_strong_bullet():
    weak = svc.select_weak_bullets(RESUME_TEXT)
    originals = [w["original"] for w in weak]
    assert not any("Led a team of 5 engineers" in o for o in originals)


def test_generate_rewrite_suggestions_no_weak_bullets_skips_api_call(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("Anthropic client should not be constructed")

    monkeypatch.setattr(svc.anthropic, "Anthropic", boom)
    resume = _fake_resume("Just a short resume with no bullet-like lines at all.")
    result = svc.generate_rewrite_suggestions(resume)
    assert result.suggestions == []


def test_generate_rewrite_suggestions_missing_key_raises_without_network_call(monkeypatch):
    monkeypatch.setattr(svc.settings, "ANTHROPIC_API_KEY", "")

    def boom(*args, **kwargs):
        raise AssertionError("Anthropic client should not be constructed when key is missing")

    monkeypatch.setattr(svc.anthropic, "Anthropic", boom)
    resume = _fake_resume()
    with pytest.raises(svc.RewriteNotConfiguredError):
        svc.generate_rewrite_suggestions(resume)


def test_generate_rewrite_suggestions_success(monkeypatch):
    monkeypatch.setattr(svc.settings, "ANTHROPIC_API_KEY", "test-key")

    weak = svc.select_weak_bullets(RESUME_TEXT)
    payload = json.dumps({"items": [{"rewritten": "Rewritten.", "rationale": "Because."} for _ in weak]})

    class FakeMessages:
        def create(self, **kwargs):
            return _fake_response(payload)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr(svc.anthropic, "Anthropic", FakeClient)
    resume = _fake_resume()
    result = svc.generate_rewrite_suggestions(resume)
    assert len(result.suggestions) == len(weak)
    assert result.suggestions[0].rewritten == "Rewritten."


def test_generate_rewrite_suggestions_rate_limit_raises_provider_error(monkeypatch):
    monkeypatch.setattr(svc.settings, "ANTHROPIC_API_KEY", "test-key")

    class FakeMessages:
        def create(self, **kwargs):
            raise _api_error(anthropic.RateLimitError, status_code=429)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr(svc.anthropic, "Anthropic", FakeClient)
    resume = _fake_resume()
    with pytest.raises(svc.RewriteProviderError):
        svc.generate_rewrite_suggestions(resume)


def test_generate_rewrite_suggestions_auth_error_raises_not_configured(monkeypatch):
    monkeypatch.setattr(svc.settings, "ANTHROPIC_API_KEY", "test-key")

    class FakeMessages:
        def create(self, **kwargs):
            raise _api_error(anthropic.AuthenticationError, status_code=401)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr(svc.anthropic, "Anthropic", FakeClient)
    resume = _fake_resume()
    with pytest.raises(svc.RewriteNotConfiguredError):
        svc.generate_rewrite_suggestions(resume)

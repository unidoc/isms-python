from __future__ import annotations

import pytest
import responses

from isms import (
    IsmsAuthError,
    IsmsClient,
    IsmsHTTPError,
    IsmsNotFoundError,
    IsmsValidationError,
)


BASE = "https://demo.isms.sh"
API = f"{BASE}/api"


@pytest.fixture()
def client() -> IsmsClient:
    return IsmsClient(BASE, "test-token")


def test_from_env_requires_credentials(monkeypatch):
    monkeypatch.delenv("ISMS_API_URL", raising=False)
    monkeypatch.delenv("ISMS_BASE_URL", raising=False)
    monkeypatch.delenv("ISMS_API_TOKEN", raising=False)
    monkeypatch.delenv("ISMS_API_KEY", raising=False)
    monkeypatch.delenv("ISMS_ENV", raising=False)
    with pytest.raises(EnvironmentError):
        IsmsClient.from_env()


def test_from_env_reads_variables(monkeypatch):
    monkeypatch.setenv("ISMS_API_URL", "https://example.isms.sh")
    monkeypatch.setenv("ISMS_API_TOKEN", "abc")
    monkeypatch.delenv("ISMS_ENV", raising=False)
    c = IsmsClient.from_env()
    assert c.base_url.endswith("/api")


def test_base_url_appends_api():
    c = IsmsClient(BASE, "t")
    assert c.base_url == API


def test_base_url_preserves_existing_api_suffix():
    c = IsmsClient(f"{BASE}/api", "t")
    assert c.base_url == f"{BASE}/api"


@responses.activate
def test_supplier_add_posts_payload(client):
    payload = {
        "name": "MaintMaster",
        "supplier_type": "saas",
        "criticality": "high",
    }
    responses.post(
        f"{API}/v1/suppliers",
        json={"id": 1, "identifier": "SUP-001", **payload},
    )

    result = client.suppliers.add(payload)

    assert result["identifier"] == "SUP-001"
    call = responses.calls[0]
    assert call.request.headers["Authorization"] == "Bearer test-token"
    assert call.request.headers["User-Agent"].startswith("isms-python/")


@responses.activate
def test_risk_add_with_references(client):
    responses.post(
        f"{API}/v1/risks",
        json={"id": 1, "identifier": "RISK-001", "title": "X"},
    )
    refs = [{"type": "document", "id": "esg-policy"}]
    client.risks.add({"title": "X"}, references=refs)

    body = responses.calls[0].request.body
    assert b'"references"' in body
    assert b"esg-policy" in body


@responses.activate
def test_reference_create(client):
    responses.post(
        f"{API}/v1/references",
        json={"id": 42},
    )
    client.references.create(
        source_type="corrective_action",
        source_id="7",
        target_type="risk",
        target_id="RISK-001",
    )
    body = responses.calls[0].request.body
    assert b"corrective_action" in body
    assert b"RISK-001" in body


@responses.activate
def test_not_found_raises(client):
    responses.get(f"{API}/v1/suppliers/nope", status=404, json={"error": "not found"})
    with pytest.raises(IsmsNotFoundError):
        client.suppliers.get("nope")


@responses.activate
def test_auth_error_raises(client):
    responses.get(f"{API}/v1/suppliers", status=401, json={"error": "unauthorized"})
    with pytest.raises(IsmsAuthError):
        client.suppliers.list()


@responses.activate
def test_validation_error_raises(client):
    responses.post(f"{API}/v1/suppliers", status=422, json={"error": "missing name"})
    with pytest.raises(IsmsValidationError):
        client.suppliers.add({})


@responses.activate
def test_generic_http_error_raises(client):
    responses.get(f"{API}/v1/suppliers", status=500, json={"error": "server down"})
    with pytest.raises(IsmsHTTPError):
        client.suppliers.list()


@responses.activate
def test_delete_returns_none(client):
    responses.delete(f"{API}/v1/suppliers/SUP-001", status=204)
    assert client.suppliers.delete("SUP-001") is None


@responses.activate
def test_list_unwraps_data_envelope(client):
    # ISMS list endpoints return {"data": [...], "total": N} — list() must
    # yield the items, not the envelope dict.
    responses.get(f"{API}/v1/suppliers", json={"data": [{"id": 1}, {"id": 2}], "total": 2})
    result = client.suppliers.list()
    assert result == [{"id": 1}, {"id": 2}]


@responses.activate
def test_list_handles_bare_array(client):
    responses.get(f"{API}/v1/risks", json=[{"id": 9}])
    assert client.risks.list() == [{"id": 9}]


@responses.activate
def test_whoami_hits_me_endpoint(client):
    # The identity endpoint is /me, not /whoami.
    responses.get(f"{API}/v1/me", json={"email": "admin@example.com"})
    assert client.whoami.get()["email"] == "admin@example.com"


@responses.activate
def test_documents_list_uses_all(client):
    responses.get(f"{API}/v1/documents/all", json={"data": [{"name": "iso27001"}]})
    assert client.documents.list() == [{"name": "iso27001"}]


@responses.activate
def test_document_body_by_id(client):
    responses.get(f"{API}/v1/documents/iso27001-4-1/body", json={"body": "# Context"})
    assert client.documents.body("iso27001-4-1")["body"] == "# Context"


@responses.activate
def test_organization_uuid_header_sent():
    # Org selection on a bare domain goes through X-Organization-UUID.
    c = IsmsClient(BASE, "t", organization_uuid="org-uuid-123")
    responses.get(f"{API}/v1/suppliers", json={"data": []})
    c.suppliers.list()
    assert responses.calls[0].request.headers["X-Organization-UUID"] == "org-uuid-123"

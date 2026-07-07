"""HTTP client for the ISMS platform.

The client speaks the ``/v1/*`` REST API of an ISMS deployment. Point it at
your instance and give it an API token:

    from isms import IsmsClient
    client = IsmsClient.from_env()

    supplier = client.suppliers.add({
        "name": "MaintMaster",
        "supplier_type": "saas",
        "criticality": "high",
        "data_access": True,
    })

Configuration precedence, high to low:

    1. Explicit constructor arguments.
    2. Environment variables ``ISMS_API_URL``/``ISMS_BASE_URL`` and
       ``ISMS_API_TOKEN``/``ISMS_API_KEY``.
    3. Optional env file pointed at by ``ISMS_ENV``.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from isms._version import __version__
from isms.env import load_env_file
from isms.exceptions import (
    IsmsAuthError,
    IsmsHTTPError,
    IsmsNotFoundError,
    IsmsValidationError,
)

_DEFAULT_TIMEOUT = 30.0
_USER_AGENT = f"isms-python/{__version__}"


def _resolve_base_url(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith("/api") or "/api/" in url + "/":
        return url
    return url + "/api"


def _as_list(payload: Any) -> list[dict]:
    """Normalize a list response to a plain list.

    The ISMS list endpoints return a ``{"data": [...], "total": N}`` envelope;
    a few return a bare array. Both collapse to the list of items here, so a
    caller always gets a ``list`` from ``.list()``.
    """
    if payload is None:
        return []
    if isinstance(payload, dict):
        data = payload.get("data")
        return data if isinstance(data, list) else []
    if isinstance(payload, list):
        return payload
    return []


class _HTTP:
    """Thin wrapper around ``requests.Session`` with ISMS conventions."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        organization_uuid: str | None = None,
        cf_client_id: str | None = None,
        cf_client_secret: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = _resolve_base_url(base_url)
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "User-Agent": _USER_AGENT,
                "Accept": "application/json",
            }
        )
        # Org selection: a subdomain URL (https://your-org.isms.sh) already scopes
        # the request server-side. This header is only needed for a multi-org token
        # on a bare domain — the server resolves it via X-Organization-UUID.
        if organization_uuid:
            self._session.headers["X-Organization-UUID"] = organization_uuid
        if cf_client_id and cf_client_secret:
            self._session.headers["CF-Access-Client-Id"] = cf_client_id
            self._session.headers["CF-Access-Client-Secret"] = cf_client_secret

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _raise(self, resp: requests.Response) -> None:
        try:
            payload = resp.json()
            message = payload.get("error") or payload.get("message") or resp.text
        except ValueError:
            payload = None
            message = resp.text or resp.reason

        cls: type[IsmsHTTPError]
        if resp.status_code in (401, 403):
            cls = IsmsAuthError
        elif resp.status_code == 404:
            cls = IsmsNotFoundError
        elif resp.status_code in (400, 422):
            cls = IsmsValidationError
        else:
            cls = IsmsHTTPError
        raise cls(resp.status_code, str(message), body=resp.text)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        resp = self._session.request(
            method,
            self._url(path),
            json=json_body,
            params=params,
            timeout=self.timeout,
        )
        if resp.status_code >= 400:
            self._raise(resp)
        if resp.status_code == 204 or not resp.content:
            return None
        try:
            return resp.json()
        except ValueError as exc:
            raise IsmsHTTPError(resp.status_code, f"invalid JSON response: {exc}", body=resp.text)

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, body: Any | None = None) -> Any:
        return self.request("POST", path, json_body=body)

    def put(self, path: str, body: Any | None = None) -> Any:
        return self.request("PUT", path, json_body=body)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)


class _Resource:
    """Base class for entity resources."""

    def __init__(self, http: _HTTP) -> None:
        self._http = http


class SupplierResource(_Resource):
    """Suppliers register (``/v1/suppliers``)."""

    def list(self) -> list[dict]:
        return _as_list(self._http.get("/v1/suppliers"))

    def get(self, supplier_id: str) -> dict:
        return self._http.get(f"/v1/suppliers/{supplier_id}")

    def add(self, data: dict) -> dict:
        return self._http.post("/v1/suppliers", data)

    def update(self, supplier_id: str, data: dict) -> dict:
        return self._http.put(f"/v1/suppliers/{supplier_id}", data)

    def delete(self, supplier_id: str) -> None:
        self._http.delete(f"/v1/suppliers/{supplier_id}")


class RiskResource(_Resource):
    """Risk register (``/v1/risks``)."""

    def list(self) -> list[dict]:
        return _as_list(self._http.get("/v1/risks"))

    def get(self, risk_id: str) -> dict:
        return self._http.get(f"/v1/risks/{risk_id}")

    def add(self, data: dict, references: list[dict] | None = None) -> dict:
        body = dict(data)
        if references:
            body["references"] = references
        return self._http.post("/v1/risks", body)

    def update(self, risk_id: str, data: dict) -> dict:
        return self._http.put(f"/v1/risks/{risk_id}", data)

    def delete(self, risk_id: str) -> None:
        self._http.delete(f"/v1/risks/{risk_id}")


class IncidentResource(_Resource):
    """Incidents and events (``/v1/incidents``)."""

    def list(self) -> list[dict]:
        return _as_list(self._http.get("/v1/incidents"))

    def get(self, incident_id: str) -> dict:
        return self._http.get(f"/v1/incidents/{incident_id}")

    def create(self, data: dict, references: list[dict] | None = None) -> dict:
        body = dict(data)
        if references:
            body["references"] = references
        return self._http.post("/v1/incidents", body)

    def update(self, incident_id: str, data: dict) -> dict:
        return self._http.put(f"/v1/incidents/{incident_id}", data)

    def delete(self, incident_id: str) -> None:
        self._http.delete(f"/v1/incidents/{incident_id}")


class CorrectiveResource(_Resource):
    """Corrective actions (``/v1/corrective-actions``)."""

    _base = "/v1/corrective-actions"

    def list(self) -> list[dict]:
        return _as_list(self._http.get(self._base))

    def get(self, ca_id: str | int) -> dict:
        return self._http.get(f"{self._base}/{ca_id}")

    def create(self, data: dict, references: list[dict] | None = None) -> dict:
        body = dict(data)
        if references:
            body["references"] = references
        return self._http.post(self._base, body)

    def update(self, ca_id: str | int, data: dict) -> dict:
        return self._http.put(f"{self._base}/{ca_id}", data)

    def set_status(self, ca_id: str | int, status: str) -> dict:
        return self._http.put(f"{self._base}/{ca_id}/status", {"status": status})

    def delete(self, ca_id: str | int) -> None:
        self._http.delete(f"{self._base}/{ca_id}")


class TaskResource(_Resource):
    """Tasks register (``/v1/tasks``)."""

    def list(self) -> list[dict]:
        return _as_list(self._http.get("/v1/tasks"))

    def get(self, task_id: str | int) -> dict:
        return self._http.get(f"/v1/tasks/{task_id}")

    def create(self, data: dict, references: list[dict] | None = None) -> dict:
        body = dict(data)
        if references:
            body["references"] = references
        return self._http.post("/v1/tasks", body)

    def update(self, task_id: str | int, data: dict) -> dict:
        return self._http.put(f"/v1/tasks/{task_id}", data)

    def set_status(self, task_id: str | int, status: str) -> dict:
        return self._http.put(f"/v1/tasks/{task_id}/status", {"status": status})

    def delete(self, task_id: str | int) -> None:
        self._http.delete(f"/v1/tasks/{task_id}")


class ReferenceResource(_Resource):
    """Cross-entity references (``/v1/references``).

    Used to link risks, incidents, corrective actions, tasks, documents, and
    other registered entities to each other after they have been created.
    """

    def list(self, *, entity_type: str | None = None, entity_id: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if entity_type:
            params["type"] = entity_type
        if entity_id:
            params["id"] = entity_id
        return _as_list(self._http.get("/v1/references", params=params or None))

    def create(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
    ) -> dict:
        return self._http.post(
            "/v1/references",
            {
                "source_type": source_type,
                "source_id": source_id,
                "target_type": target_type,
                "target_id": target_id,
            },
        )

    def delete(self, reference_id: str | int) -> None:
        self._http.delete(f"/v1/references/{reference_id}")


class DocumentResource(_Resource):
    """Documents (``/v1/documents``)."""

    def list(self) -> list[dict]:
        """The document tree (folders with their documents)."""
        return _as_list(self._http.get("/v1/documents/all"))

    def search(self, query: str) -> list[dict]:
        return _as_list(self._http.get("/v1/documents/search", params={"q": query}))

    def body(self, document_id: str) -> dict:
        """A document's rendered body + metadata, by document_id."""
        return self._http.get(f"/v1/documents/{document_id}/body")


class WhoamiResource(_Resource):
    """Identity of the current API token (``/v1/me``)."""

    def get(self) -> dict:
        return self._http.get("/v1/me")


class IsmsClient:
    """Client for the ISMS platform."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        organization_uuid: str | None = None,
        cf_client_id: str | None = None,
        cf_client_secret: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")
        self._http = _HTTP(
            base_url,
            token,
            organization_uuid=organization_uuid,
            cf_client_id=cf_client_id,
            cf_client_secret=cf_client_secret,
            timeout=timeout,
            session=session,
        )
        self.suppliers = SupplierResource(self._http)
        self.risks = RiskResource(self._http)
        self.incidents = IncidentResource(self._http)
        self.correctives = CorrectiveResource(self._http)
        self.tasks = TaskResource(self._http)
        self.references = ReferenceResource(self._http)
        self.documents = DocumentResource(self._http)
        self.whoami = WhoamiResource(self._http)

    @property
    def base_url(self) -> str:
        return self._http.base_url

    @classmethod
    def from_env(
        cls,
        *,
        env_file: str | os.PathLike[str] | None = None,
        override: bool = False,
    ) -> IsmsClient:
        """Construct a client from environment variables.

        Reads ``ISMS_API_URL`` (or ``ISMS_BASE_URL``) and ``ISMS_API_TOKEN``
        (or ``ISMS_API_KEY``). Optionally loads an env file first: if
        ``env_file`` is passed it is used, otherwise the path in
        ``ISMS_ENV`` is used if set.
        """
        env_path = env_file or os.environ.get("ISMS_ENV")
        if env_path:
            load_env_file(env_path, override=override)

        base_url = os.environ.get("ISMS_API_URL") or os.environ.get("ISMS_BASE_URL")
        token = os.environ.get("ISMS_API_TOKEN") or os.environ.get("ISMS_API_KEY")
        if not base_url or not token:
            raise EnvironmentError(
                "ISMS_API_URL (or ISMS_BASE_URL) and ISMS_API_TOKEN (or ISMS_API_KEY) "
                "must be set, either directly or via an env file pointed at by ISMS_ENV."
            )
        return cls(
            base_url,
            token,
            organization_uuid=os.environ.get("ISMS_ORGANIZATION_UUID") or None,
            cf_client_id=os.environ.get("CF_ACCESS_CLIENT_ID") or None,
            cf_client_secret=os.environ.get("CF_ACCESS_CLIENT_SECRET") or None,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"IsmsClient(base_url={self._http.base_url!r})"

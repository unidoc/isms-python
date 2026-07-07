# isms

Official Python client for the [ISMS platform](https://isms.sh).

ISMS is the open Information Security Management System that keeps policies,
controls, risks, suppliers, incidents, and evidence in one place with a
scriptable API. This library gives you the same surface as the `isms` CLI and
the Go client, from Python, so you can seed data, automate audits, and build
custom dashboards without touching the web UI.

## Install

```sh
pip install isms
```

Requires Python 3.10 or later.

## Configure

Point the client at your ISMS deployment and give it an API token:

```sh
export ISMS_API_URL=https://your-org.isms.sh
export ISMS_API_TOKEN=<api-token>
export ISMS_ORGANIZATION=<org-slug>   # only if your token spans multiple orgs
```

Create the token from an admin session with `isms server api-key create`
(CLI) or from the web UI. If your deployment sits behind Cloudflare Access,
also set `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET`.

If you already have an ISMS env file (`KEY=VALUE` per line, the same format
the CLI reads), point `ISMS_ENV` at it and the client will load it for you:

```sh
export ISMS_ENV=/path/to/isms.env
```

## Quickstart

```python
from isms import IsmsClient

client = IsmsClient.from_env()

# Confirm the token
print(client.whoami.get())

# Add a supplier
supplier = client.suppliers.add({
    "name": "MaintMaster",
    "supplier_type": "saas",
    "criticality": "high",
    "data_access": True,
    "notes": "CMMS platform used across terminals.\n\n## Services\nMaintenance planning and work orders.",
})
print(supplier["identifier"], supplier["name"])

# Add a risk that came out of a leadership review
risk = client.risks.add({
    "title": "Environmental and sustainability governance gap",
    "description": "CSRD scope maturing; no environmental policy in the IMS.",
    "risk_type": "threat",
    "origin": "external",
    "category": "grc",
    "current_likelihood": 3,
    "current_impact": 3,
    "treatment": "mitigate",
    "status": "open",
})

# Record the event that surfaced the risk, and link them
event = client.incidents.create(
    {
        "title": "External stakeholder feedback on ESG governance",
        "description": "Financier lunch briefing raised ESG position and CSRD readiness.",
        "severity": "low",
        "source": "external",
        "incident_type": "event",
    },
    references=[{"type": "risk", "id": risk["identifier"]}],
)

# Track the treatment as a corrective action
ca = client.correctives.create({
    "title": "Publish substantive public sustainability page",
    "description": "Dedicated /sustainability page on stsplatform.com.",
    "source": "feedback",
    "severity": "observation",
})

# Explicit reference between the CA and the risk (in case the create-time
# reference flags are not yet available in your ISMS version).
client.references.create(
    source_type="corrective_action",
    source_id=str(ca["id"]),
    target_type="risk",
    target_id=risk["identifier"],
)
```

## Resources

Each entity register is exposed as a namespace on the client:

| Namespace | Purpose |
|---|---|
| `client.suppliers` | Supplier register |
| `client.risks` | Risk register |
| `client.incidents` | Incidents and events register |
| `client.correctives` | Corrective actions |
| `client.tasks` | Task register |
| `client.references` | Cross-entity references |
| `client.documents` | Document library |
| `client.whoami` | Identity of the current API token |

All resources expose `list()` and, where the API supports it, `get(id)`,
`add(data)` / `create(data)`, `update(id, data)`, and `delete(id)`.

## Errors

All errors inherit from `isms.IsmsError`:

- `IsmsAuthError` — 401/403
- `IsmsNotFoundError` — 404
- `IsmsValidationError` — 400/422
- `IsmsHTTPError` — other non-2xx responses

## Development

```sh
git clone https://github.com/unidoc/isms-python
cd isms-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Licence

Apache 2.0. See `LICENSE`.

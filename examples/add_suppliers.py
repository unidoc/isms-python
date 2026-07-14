import sys

from isms import IsmsClient, IsmsError

try:
    client = IsmsClient.from_env()
except EnvironmentError as e:
    sys.exit(f"{e}\n\nSee examples/README.md for setup.")

# Supplier notes are markdown — keep them as readable triple-quoted blocks rather
# than concatenated string fragments. Fictional vendors so the example doesn't
# assert real, time-sensitive compliance facts that would drift out of date.

ACME_NOTES = """\
Hosted CRM used by the sales team for customer records and pipeline data.

## Services
CRM web app and REST API.

## Data protection
SOC 2 Type II. GDPR-compliant Data Processing Addendum with Standard
Contractual Clauses for EU-to-US transfers.
"""

GLOBEX_NOTES = """\
Colocation and managed servers for the internal wiki and build infrastructure.

## Services
Managed VMs, backups, and network.

## Data protection
ISO 27001 certified. Annual penetration test; no access to production
customer data.
"""

suppliers = [
    {
        "name": "Acme Cloud SaaS",
        "supplier_type": "saas",
        "criticality": "high",
        "data_access": True,
        "contact": "https://trust.acme-cloud.example",
        "confidentiality": 5,
        "integrity": 4,
        "availability": 4,
        "notes": ACME_NOTES,
    },
    {
        "name": "Globex Managed Hosting",
        "supplier_type": "hosting",
        "criticality": "medium",
        "data_access": False,
        "contact": "https://trust.globex.example",
        "confidentiality": 3,
        "integrity": 4,
        "availability": 5,
        "notes": GLOBEX_NOTES,
    },
]

# Re-running adds these again — it's a demo, not idempotent.
added = 0
for s in suppliers:
    try:
        result = client.suppliers.add(s)
    except IsmsError as e:
        print(f"!  {s['name']}: {e}")
        continue
    added += 1
    print(f"{result['identifier']}  {result['name']}  "
          f"C{result['confidentiality']} I{result['integrity']} "
          f"A{result['availability']}")

print(f"\nAdded {added} of {len(suppliers)} suppliers.")

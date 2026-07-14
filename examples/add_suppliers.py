from isms import IsmsClient, IsmsError

client = IsmsClient.from_env()

suppliers = [
    {
        "name": "Anthropic",
        "supplier_type": "saas",
        "criticality": "high",
        "data_access": True,
        "contact": "https://trust.anthropic.com",
        "confidentiality": 5,
        "integrity": 4,
        "availability": 4,
        "notes": (
            "Claude API for AI-assisted drafting and evaluation across the "
            "management system.\n\n"
            "## Services\n"
            "Claude API (Opus, Sonnet, Haiku) accessed over REST.\n\n"
            "## Data protection\n"
            "SOC 2 Type II. GDPR-compliant Data Processing Addendum with "
            "Standard Contractual Clauses for EU-to-US transfers. Zero "
            "data retention available on request for enterprise plans."
        ),
    },
    {
        "name": "Microsoft",
        "supplier_type": "saas",
        "criticality": "high",
        "data_access": True,
        "contact": "https://servicetrust.microsoft.com",
        "confidentiality": 5,
        "integrity": 4,
        "availability": 5,
        "notes": (
            "Microsoft 365 tenant for email, collaboration, identity, and "
            "business data storage.\n\n"
            "## Services\n"
            "Exchange Online, Teams, SharePoint, OneDrive, Entra ID.\n\n"
            "## Data protection\n"
            "ISO 27001, ISO 27017, ISO 27018, SOC 2 Type II. GDPR-compliant "
            "DPA via Microsoft Product Terms with Standard Contractual "
            "Clauses. EU-US Data Privacy Framework certified. EU data "
            "residency available."
        ),
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

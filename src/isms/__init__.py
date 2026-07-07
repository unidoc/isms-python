"""Official Python client for the ISMS platform (isms.sh).

Quickstart:

    from isms import IsmsClient

    client = IsmsClient.from_env()
    supplier = client.suppliers.add({
        "name": "MaintMaster",
        "supplier_type": "saas",
        "criticality": "high",
        "data_access": True,
    })
"""

from isms._version import __version__
from isms.client import IsmsClient
from isms.env import load_env_file
from isms.exceptions import (
    IsmsAuthError,
    IsmsError,
    IsmsHTTPError,
    IsmsNotFoundError,
    IsmsValidationError,
)

__all__ = [
    "IsmsClient",
    "IsmsError",
    "IsmsAuthError",
    "IsmsHTTPError",
    "IsmsNotFoundError",
    "IsmsValidationError",
    "load_env_file",
    "__version__",
]

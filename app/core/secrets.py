"""Azure Key Vault secret loader.

Env values matching `@kv:<secret-name>` are resolved against the Key Vault
specified by `AZURE_KEY_VAULT_URL` using `DefaultAzureCredential` (which
picks Managed Identity in Azure, az-login locally). Resolution happens once
at process startup so subsequent `Settings()` reads see clear text.

We never log the resolved secret values.
"""

from __future__ import annotations

import os
import re

from app.core.logging import get_logger

log = get_logger(__name__)

_KV_PREFIX_RE = re.compile(r"^@kv:(?P<name>[A-Za-z0-9\-]+)$")


def hydrate_env_from_key_vault(vault_url: str) -> int:
    """Replace every `@kv:<name>` in `os.environ` with the secret's value.

    Returns the number of variables resolved. Does nothing (returns 0) if
    `vault_url` is empty so callers can wire this unconditionally.
    """
    if not vault_url:
        return 0
    # Imported lazily so the azure SDK is not required at import time
    # (tests that never touch a vault don't need it on the import path).
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)

    resolved = 0
    for env_name, value in list(os.environ.items()):
        match = _KV_PREFIX_RE.match(value or "")
        if not match:
            continue
        secret_name = match.group("name")
        try:
            secret = client.get_secret(secret_name)
        except Exception as exc:
            log.warning(
                "key_vault_secret_unavailable",
                env=env_name,
                secret=secret_name,
                error=str(exc),
            )
            continue
        os.environ[env_name] = secret.value or ""
        resolved += 1
        log.info("key_vault_secret_resolved", env=env_name, secret=secret_name)
    return resolved

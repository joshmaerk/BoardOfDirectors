from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Entra
    azure_tenant_id: str = ""
    azure_api_audience: str = ""
    # Optional allow-list of tenant ids accepted in the JWT `tid` claim,
    # comma-separated. If empty, `azure_tenant_id` is the only accepted tenant.
    azure_allowed_tenants: str = ""
    # Roles required for board.* endpoints, comma-separated. If empty, any
    # authenticated user passes (helpful for dev tenants without role assignments).
    required_api_roles: str = ""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployments: dict[str, str] = Field(default_factory=dict)

    # Azure AI Foundry (Claude via Models-as-a-Service)
    azure_ai_foundry_endpoint: str = ""
    azure_ai_foundry_api_key: str = ""
    azure_ai_foundry_deployments: dict[str, str] = Field(default_factory=dict)

    # Provider routing: model-name prefix -> provider id.
    # Defaults route "gpt-*" to Azure OpenAI, "claude-*" to Azure AI Foundry.
    llm_provider_map: dict[str, str] = Field(
        default_factory=lambda: {"gpt-": "azure-openai", "claude-": "azure-anthropic"}
    )

    # DB
    database_url: str = "postgresql+asyncpg://bod:bod@localhost:5432/bod"

    # API
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])
    log_level: str = "INFO"
    auth_dev_bypass: bool = False
    expose_openapi_docs: bool = True

    # Azure Key Vault (optional). When set, secrets that look like
    # `@kv:<secret-name>` in env are resolved from the vault on startup.
    azure_key_vault_url: str = ""

    @field_validator(
        "azure_openai_deployments",
        "azure_ai_foundry_deployments",
        "llm_provider_map",
        mode="before",
    )
    @classmethod
    def _parse_json_map(cls, v: object) -> object:
        if isinstance(v, str) and v.strip():
            return json.loads(v)
        return v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    @property
    def accepted_tenants(self) -> list[str]:
        explicit = self._split_csv(self.azure_allowed_tenants)
        if explicit:
            return explicit
        return [self.azure_tenant_id] if self.azure_tenant_id else []

    @property
    def required_api_role_names(self) -> list[str]:
        return self._split_csv(self.required_api_roles)

    @property
    def jwks_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/discovery/v2.0/keys"

    @property
    def issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/v2.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()

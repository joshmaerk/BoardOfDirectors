from __future__ import annotations

from pydantic import BaseModel


class UserOut(BaseModel):
    oid: str
    username: str
    name: str | None = None
    roles: list[str] = []

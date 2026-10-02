"""Request context. Tenant and user come from the verified session, never from model output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    REQUESTER = "requester"
    BUYER = "buyer"
    ADMIN = "admin"


_RANK = {Role.REQUESTER: 0, Role.BUYER: 1, Role.ADMIN: 2}


@dataclass(frozen=True)
class Ctx:
    tenant_id: str
    user_id: str
    role: Role

    @property
    def actor(self) -> str:
        return f"user:{self.user_id}"

    def at_least(self, role: Role) -> bool:
        return _RANK[self.role] >= _RANK[role]


class Forbidden(Exception):
    """Caller's role is insufficient."""


def require(ctx: Ctx, role: Role) -> None:
    if not ctx.at_least(role):
        raise Forbidden(f"requires role {role.value}")

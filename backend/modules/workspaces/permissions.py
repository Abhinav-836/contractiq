"""
Roles, from least to most access:

  viewer  — read contracts, analyses, obligations and alerts
  member  — + upload, re-analyse, edit obligations, handle alerts,
              delete contracts they uploaded
  admin   — + delete any contract, rename the workspace, invite people,
              manage members and viewers
  owner   — + manage admins, delete the workspace. Exactly one per workspace.
"""
from dataclasses import dataclass

from fastapi import HTTPException

ROLES = ("viewer", "member", "admin", "owner")
RANK = {role: i for i, role in enumerate(ROLES)}
# Roles that can be given through an invite or a role change (ownership isn't transferable yet).
ASSIGNABLE_ROLES = ("admin", "member", "viewer")


def at_least(role: str, minimum: str) -> bool:
    return RANK.get(role, -1) >= RANK[minimum]


@dataclass(frozen=True)
class WorkspaceContext:
    """Who is calling, in which workspace, with what role."""
    user_id: str
    workspace_id: str
    role: str

    def can(self, minimum: str) -> bool:
        return at_least(self.role, minimum)

    def require(self, minimum: str, message: str) -> None:
        if not self.can(minimum):
            raise HTTPException(403, message)


def can_manage(actor_role: str, target_role: str) -> bool:
    """
    Whether actor may change or remove someone with target_role.
    Owners manage everyone except the owner; admins manage members and viewers.
    """
    if target_role == "owner":
        return False
    if actor_role == "owner":
        return True
    return actor_role == "admin" and target_role in ("member", "viewer")


def can_grant(actor_role: str, new_role: str) -> bool:
    """Whether actor may give someone new_role (by invite or role change)."""
    if new_role not in ASSIGNABLE_ROLES:
        return False
    if actor_role == "owner":
        return True
    return actor_role == "admin" and new_role in ("member", "viewer")

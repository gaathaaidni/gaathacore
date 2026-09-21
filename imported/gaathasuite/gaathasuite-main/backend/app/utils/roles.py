from typing import Dict

ROLE_SUPERADMIN = "superadmin"
ROLE_ORGADMIN = "orgadmin"
ROLE_MANAGER = "manager"
ROLE_LEAD = "lead"
ROLE_AUDITOR = "auditor"
ROLE_PARTNER = "partner"
ROLE_STANDARD_USER = "standard_user"
ROLE_USER = "user"

ROLE_ALIASES: Dict[str, str] = {
    "superadmin": ROLE_SUPERADMIN,
    "super_admin": ROLE_SUPERADMIN,
    "orgadmin": ROLE_ORGADMIN,
    "org_admin": ROLE_ORGADMIN,
    "manager": ROLE_MANAGER,
    "lead": ROLE_LEAD,
    "auditor": ROLE_AUDITOR,
    "partner": ROLE_PARTNER,
    "standarduser": ROLE_STANDARD_USER,
    "standard_user": ROLE_STANDARD_USER,
    "user": ROLE_USER,
    "member": ROLE_STANDARD_USER,
    "admin": ROLE_ORGADMIN,
}


def normalize_role(role: str) -> str:
    return (role or "").strip().replace("-", "").replace("_", "").lower()


def canonical_role(role: str) -> str:
    normalized = normalize_role(role)
    return ROLE_ALIASES.get(normalized, normalized)


def is_superadmin(role: str) -> bool:
    return canonical_role(role) == ROLE_SUPERADMIN


def is_orgadmin(role: str) -> bool:
    return canonical_role(role) == ROLE_ORGADMIN


def is_manager_or_lead(role: str) -> bool:
    canonical = canonical_role(role)
    return canonical in {ROLE_MANAGER, ROLE_LEAD}


def is_auditor(role: str) -> bool:
    return canonical_role(role) == ROLE_AUDITOR


def is_partner(role: str) -> bool:
    return canonical_role(role) == ROLE_PARTNER


def is_standard_user(role: str) -> bool:
    return canonical_role(role) in {ROLE_STANDARD_USER, ROLE_USER}

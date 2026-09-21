from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.books import Account, JournalEntry, JournalLine


class JournalValidationError(ValueError):
    pass


def _as_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise JournalValidationError(f"Invalid monetary value: {value!r}")


async def post_journal_entry(db: AsyncSession, org_id: int, description: str, lines: Sequence[dict]) -> JournalEntry:
    if not lines:
        raise JournalValidationError("Journal entry must contain at least one line")

    normalized_lines: list[dict] = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for line in lines:
        account_id = line.get("account_id")
        if account_id is None:
            raise JournalValidationError("Each journal line requires an account_id")

        debit = _as_decimal(line.get("debit") or 0)
        credit = _as_decimal(line.get("credit") or 0)

        if debit < 0 or credit < 0:
            raise JournalValidationError("Debit and credit values cannot be negative")
        if debit and credit:
            raise JournalValidationError("Each journal line cannot contain both debit and credit")

        account = await db.get(Account, account_id)
        if account is None or account.organization_id != org_id:
            raise JournalValidationError("Journal account is invalid for this organization")

        total_debit += debit
        total_credit += credit
        normalized_lines.append({
            "account_id": account_id,
            "debit": float(debit),
            "credit": float(credit),
            "description": line.get("description") or description,
        })

    if total_debit == 0 and total_credit == 0:
        raise JournalValidationError("Journal entry cannot be empty")
    if total_debit != total_credit:
        raise JournalValidationError(
            f"Journal entry is unbalanced: debit={total_debit} credit={total_credit}"
        )

    entry = JournalEntry(
        organization_id=org_id,
        description=description,
        status="posted",
    )
    db.add(entry)

    for line in normalized_lines:
        db.add(
            JournalLine(
                entry=entry,
                account_id=line["account_id"],
                organization_id=org_id,
                debit=line["debit"],
                credit=line["credit"],
                description=line["description"],
            )
        )

    await db.flush()
    return entry

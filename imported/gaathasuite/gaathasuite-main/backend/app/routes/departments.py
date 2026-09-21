from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional
from pydantic import BaseModel

from app.utils.dependencies import get_db, require_roles
from app.utils.roles import ROLE_ORGADMIN, ROLE_SUPERADMIN
from app.models.user import User

router = APIRouter(prefix="/departments", tags=["Departments"])


class DepartmentCreateRequest(BaseModel):
    name: str
    manager_id: Optional[int] = None
    organization_id: Optional[int] = None


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = None
    manager_id: Optional[int] = None


@router.get("")
async def list_departments(
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    try:
        if getattr(current_user, 'role', '') == ROLE_SUPERADMIN:
            res = await db.execute(text("SELECT id, name, organization_id, manager_id, created_at FROM department ORDER BY name"))
        else:
            res = await db.execute(
                text("SELECT id, name, organization_id, manager_id, created_at FROM department WHERE organization_id = :org_id ORDER BY name"),
                {"org_id": current_user.organization_id}
            )
        rows = res.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("")
async def create_department(
    payload: DepartmentCreateRequest,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    try:
        if getattr(current_user, 'role', '') == ROLE_SUPERADMIN:
            organization_id = payload.organization_id
            if organization_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="organization_id is required for superadmins")
        else:
            if payload.organization_id is not None and payload.organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create department for another organization",
                )
            organization_id = current_user.organization_id

        res = await db.execute(
            text("INSERT INTO department (name, organization_id, manager_id, created_at) VALUES (:name, :org_id, :manager_id, now()) RETURNING id, name"),
            {"name": payload.name, "org_id": organization_id, "manager_id": payload.manager_id}
        )
        row = res.fetchone()
        await db.commit()
        return dict(row) if row else {"id": None, "name": payload.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{dept_id}")
async def update_department(
    dept_id: int,
    payload: DepartmentUpdateRequest,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check exists and org scope
        query = "SELECT id, organization_id FROM department WHERE id = :id"
        res = await db.execute(text(query), {"id": dept_id})
        row = res.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        if getattr(current_user, 'role', '') != ROLE_SUPERADMIN and row.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify department from another organization")

        await db.execute(
            text("UPDATE department SET name = COALESCE(:name, name), manager_id = COALESCE(:manager_id, manager_id) WHERE id = :id"),
            {"id": dept_id, "name": payload.name, "manager_id": payload.manager_id}
        )
        await db.commit()
        res = await db.execute(text("SELECT id, name, organization_id, manager_id FROM department WHERE id = :id"), {"id": dept_id})
        return dict(res.fetchone())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{dept_id}")
async def delete_department(dept_id: int, current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)), db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(text("SELECT id, organization_id FROM department WHERE id = :id"), {"id": dept_id})
        row = res.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        if getattr(current_user, 'role', '') != ROLE_SUPERADMIN and row.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete department from another organization")
        await db.execute(text("DELETE FROM department WHERE id = :id"), {"id": dept_id})
        await db.commit()
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

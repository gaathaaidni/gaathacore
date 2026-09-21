from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.legal import LegalAcceptance, LegalDocument
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/legal", tags=["Legal"])


class LegalDocumentRead(BaseModel):
    slug: str
    title: str
    version: str
    effective_date: date
    content: str

    class Config:
        from_attributes = True


class LegalAcceptanceCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=40)


class LegalAcceptanceRead(BaseModel):
    slug: str
    version: str
    accepted_at: str


@router.get("/documents", response_model=List[LegalDocumentRead])
async def list_published_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LegalDocument)
        .where(LegalDocument.published.is_(True))
        .order_by(LegalDocument.slug)
    )
    return result.scalars().all()


@router.get("/documents/{slug}", response_model=LegalDocumentRead)
async def get_published_document(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LegalDocument).where(
            LegalDocument.slug == slug,
            LegalDocument.published.is_(True),
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal document not found")
    return document


@router.post("/acceptances", response_model=LegalAcceptanceRead, status_code=status.HTTP_201_CREATED)
async def accept_document(
    payload: LegalAcceptanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LegalDocument).where(
            LegalDocument.slug == payload.slug,
            LegalDocument.version == payload.version,
            LegalDocument.published.is_(True),
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Published legal version is not available")

    existing_result = await db.execute(
        select(LegalAcceptance).where(
            LegalAcceptance.user_id == current_user.id,
            LegalAcceptance.document_id == document.id,
            LegalAcceptance.version == document.version,
        )
    )
    acceptance = existing_result.scalar_one_or_none()
    if acceptance is None:
        acceptance = LegalAcceptance(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            document_id=document.id,
            version=document.version,
        )
        db.add(acceptance)
        await db.commit()
        await db.refresh(acceptance)

    return {
        "slug": document.slug,
        "version": acceptance.version,
        "accepted_at": acceptance.accepted_at.isoformat(),
    }


@router.get("/acceptances/me", response_model=List[LegalAcceptanceRead])
async def list_my_acceptances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LegalAcceptance, LegalDocument.slug)
        .join(LegalDocument, LegalDocument.id == LegalAcceptance.document_id)
        .where(LegalAcceptance.user_id == current_user.id)
        .order_by(LegalAcceptance.accepted_at.desc())
    )
    return [
        {"slug": slug, "version": acceptance.version, "accepted_at": acceptance.accepted_at.isoformat()}
        for acceptance, slug in result.all()
    ]

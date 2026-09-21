from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.models.crm import Lead, Customer
from app.models.notifications import Notification
from app.models.organization import Organization
# from extensions import socketio # SocketIO will be refactored for FastAPI
from app.models.user import User
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
    ROLE_SUPERADMIN,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


async def resolve_effective_org_id(db: AsyncSession, current_user: User) -> int:
    """Return a valid tenant org id for the caller, creating a default org when needed."""
    org_id = getattr(current_user, 'organization_id', None)
    if org_id is not None:
        return org_id

    if not getattr(current_user, 'is_superadmin', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Organization context is missing for current user')

    org_result = await db.execute(select(Organization).order_by(Organization.id.asc()).limit(1))
    org = org_result.scalar_one_or_none()
    if org is None:
        org = Organization(name='Default Organization', slug='default-organization')
        db.add(org)
        await db.flush()

    current_user.organization_id = org.id
    return org.id


@router.get('/api/leads')
async def get_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    ))
):
    """API endpoint to get a list of leads."""
    org_id = current_user.organization_id
    is_god = current_user.role == ROLE_SUPERADMIN
    query = select(Lead)
    if not is_god:
        query = query.where(Lead.organization_id == org_id)

    result = await db.execute(query)
    leads = result.scalars().all()
    return [{
        'id': lead.id,
        'name': lead.name,
        'email': getattr(lead, 'email', lead.contact_email),
        'company': lead.company,
        'status': lead.status
    } for lead in leads]

@router.post('/api/leads', status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    """API endpoint to create a new lead."""
    org_id = await resolve_effective_org_id(db, current_user)

    name = payload.get('name')
    if not name or not str(name).strip():
        raise HTTPException(status_code=400, detail='Lead name is required.')

    contact_email = payload.get('contact_email') or payload.get('email')
    company = payload.get('company')
    source = payload.get('source') or 'Website'

    new_lead = Lead(
        organization_id=org_id,
        name=str(name).strip(),
        contact_email=str(contact_email).strip() if contact_email else None,
        company=str(company).strip() if company else None,
        source=str(source).strip(),
        status='new'
    )
    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)

    return {
        'id': new_lead.id,
        'name': new_lead.name,
        'email': new_lead.contact_email,
        'company': new_lead.company,
        'status': new_lead.status,
        'source': new_lead.source
    }

@router.post('/api/convert-lead/{lead_id}')
async def convert_lead(
    lead_id: int, 
    db: AsyncSession = Depends(get_db), # Use the new async db dependency
    current_user: User = Depends(require_roles(
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    ))
):
    """API endpoint to convert a lead to a customer."""
    org_id = await resolve_effective_org_id(db, current_user)
    is_god = current_user.role == ROLE_SUPERADMIN
    query = select(Lead).where(Lead.id == lead_id)
    if not is_god:
        query = query.where(Lead.organization_id == org_id)

    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status == 'converted':
        raise HTTPException(status_code=400, detail="This lead has already been converted.")

    # 1. Create a new Customer record
    customer = Customer(
        name=lead.name,
        email=lead.contact_email,
        company=lead.company,
        lead_id=lead.id,
        organization_id=current_user.organization_id
    )
    db.add(customer)
    # ... logic continues with async db.commit()
    
    # 2. Update the Lead status
    lead.status = 'converted'
    
    # 3. Create persistent notification (assuming Notification model is updated)
    # notif_msg = f'Success: {lead.name} has been converted to a customer.'
    # new_notif = Notification(
    #     user_id=current_user.id, # This will need to be current_user.id
    #     title="Lead Converted",
    #     body=notif_msg,
    #     is_read=False
    # )
    # db.add(new_notif)
    
    await db.commit()
    # await db.refresh(new_notif) # If notification is added
    await db.refresh(customer)
    
    # 4. Emit a WebSocket event (will need FastAPI-SocketIO integration)
    # user_room = f"user_{current_user.id}"
    # socketio.emit('notification', {
    #     'msg': notif_msg,
    #     'type': 'success',
    #     'customer_id': customer.id
    # }, room=user_room)

    return {"message": "Lead converted to customer successfully", "customer_id": customer.id}
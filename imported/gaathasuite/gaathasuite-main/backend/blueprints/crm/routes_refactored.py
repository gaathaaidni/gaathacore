from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.models.crm import Customer, Lead, Opportunity
from app.models.user import User
from app.schemas.crm import (
    CustomerCreate,
    CustomerRead,
    LeadCreate,
    LeadRead,
    LeadUpdate,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
)
from app.utils.dependencies import get_org_db_session, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_PARTNER,
    ROLE_STANDARD_USER,
    ROLE_SUPERADMIN,
)

router = APIRouter(prefix="/api/v2/crm", tags=["CRM"])


@router.get("/leads", response_model=List[LeadRead])
async def list_leads(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_PARTNER,
        ROLE_STANDARD_USER, ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, is_god = db_context
    query = select(Lead).order_by(Lead.id.desc())
    if not is_god:
        query = query.where(Lead.organization_id == org_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(require_roles(ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, _ = db_context
    lead = Lead(**lead_in.model_dump(), organization_id=org_id, status="new")
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: User = Depends(require_roles(ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, is_god = db_context
    query = select(Lead).where(Lead.id == lead_id)
    if not is_god:
        query = query.where(Lead.organization_id == org_id)
    lead = (await db.execute(query)).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in lead_in.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/opportunities", response_model=List[OpportunityRead])
async def list_opportunities(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_PARTNER,
        ROLE_STANDARD_USER, ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, is_god = db_context
    query = select(Opportunity).order_by(Opportunity.id.desc())
    if not is_god:
        query = query.where(Opportunity.organization_id == org_id)
    return (await db.execute(query)).scalars().all()


@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opportunity_in: OpportunityCreate,
    current_user: User = Depends(require_roles(ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, _ = db_context
    customer = (await db.execute(select(Customer).where(
        Customer.id == opportunity_in.customer_id, Customer.organization_id == org_id
    ))).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in your organization")
    opportunity = Opportunity(**opportunity_in.model_dump(), organization_id=org_id)
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    return opportunity


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: int,
    opportunity_in: OpportunityUpdate,
    current_user: User = Depends(require_roles(ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db_context: tuple = Depends(get_org_db_session),
):
    db, org_id, is_god = db_context
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    if not is_god:
        query = query.where(Opportunity.organization_id == org_id)
    opportunity = (await db.execute(query)).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    for field, value in opportunity_in.model_dump(exclude_unset=True).items():
        setattr(opportunity, field, value)
    await db.commit()
    await db.refresh(opportunity)
    return opportunity

@router.get("/customers", response_model=List[CustomerRead])
async def list_customers(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Retrieve customers with pagination. Super Admin (God) sees everything."""
    db, org_id, is_god = db_context
    offset = (page - 1) * limit
    
    query = select(Customer)
    if not is_god:
        query = query.where(Customer.organization_id == org_id)
    
    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Create customer. God must still provide an org_id in the body or header."""
    db, org_id, is_god = db_context
    
    # If God is creating, we use the org_id from header if provided, otherwise default
    target_org_id = org_id if org_id else 1 
    
    new_customer = Customer(
        **customer_in.model_dump(),
        organization_id=target_org_id
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    return new_customer

@router.get("/customers/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_PARTNER,
        ROLE_STANDARD_USER,
        ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    db, org_id, is_god = db_context
    
    query = select(Customer).where(Customer.id == customer_id)
    
    # God ignores the organization ownership check
    if not is_god:
        query = query.where(Customer.organization_id == org_id)
        
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found in your organization")
    return customer

@router.post("/convert-lead/{lead_id}", status_code=status.HTTP_200_OK)
async def convert_lead_to_customer(
    lead_id: int,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER,
        ROLE_LEAD,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Atomic conversion of Lead to Customer in the async FastAPI stack."""
    db, org_id, is_god = db_context
    
    # Fetch Lead
    lead_stmt = select(Lead).where(Lead.id == lead_id)
    if not is_god:
        lead_stmt = lead_stmt.where(Lead.organization_id == org_id)
    res = await db.execute(lead_stmt)
    lead = res.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status == 'converted':
        raise HTTPException(status_code=400, detail="Lead already converted")
        
    # Create Customer
    new_customer = Customer(
        name=lead.name,
        email=lead.contact_email,
        company=lead.company,
        organization_id=org_id
    )
    db.add(new_customer)
    
    # Update Lead
    lead.status = 'converted'
    
    await db.commit()
    return {"message": "Lead converted successfully", "customer_id": new_customer.id}
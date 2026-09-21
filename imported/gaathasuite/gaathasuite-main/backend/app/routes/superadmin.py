import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

import json
from app.db import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.organization import Organization
from app.utils.roles import ROLE_ORGADMIN
from ..models.coupon import Coupon

router = APIRouter(
    prefix="/api/superadmin",
    tags=["Superadmin"],
)

def require_superadmin(current_user: User = Depends(get_current_user)):
    """
    Dependency that checks if the current user is a superadmin.
    """
    if not current_user or not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="You do not have permission to access this resource.")
    return current_user

@router.get("/dashboard-stats", dependencies=[Depends(require_superadmin)])
async def get_superadmin_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Endpoint to fetch statistics for the god-level dashboard.
    """
    total_orgs_result = await db.execute(select(func.count(Organization.id)))
    total_users_result = await db.execute(select(func.count(User.id)))
    
    # Placeholder for active subscriptions. In a real system, this would query a subscription table.
    # For now, we'll count active organizations.
    active_subs_result = await db.execute(select(func.count(Organization.id)).where(Organization.is_active == True))

    return {
        "total_organizations": total_orgs_result.scalar_one_or_none() or 0,
        "total_users": total_users_result.scalar_one_or_none() or 0,
        "active_subscriptions": active_subs_result.scalar_one_or_none() or 0
    }

@router.get("/organizations", dependencies=[Depends(require_superadmin)])
async def list_organizations(
    db: AsyncSession = Depends(get_db), 
    page: int = 1, 
    per_page: int = 10,
    sort_by: str = 'created_at',
    sort_order: str = 'desc',
    search: str | None = None
):
    """
    Lists all organizations in the system for the superadmin dashboard.
    """
    offset = (page - 1) * per_page

    # Subquery to find the last login for an admin in each organization
    last_login_subquery = (
        select(
            User.organization_id,
            func.max(User.last_login_at).label("last_login_at")
        )
        .where(User.role == ROLE_ORGADMIN)
        .group_by(User.organization_id)
        .subquery()
    )

    # Base query
    query = select(Organization, last_login_subquery.c.last_login_at).outerjoin(last_login_subquery, Organization.id == last_login_subquery.c.organization_id)
    count_query = select(func.count(Organization.id))

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(Organization.name.ilike(search_term))
        count_query = count_query.where(Organization.name.ilike(search_term))

    sortable_columns = {c.key for c in class_mapper(Organization).columns} | {'last_login_at'}
    if sort_by not in sortable_columns:
        sort_by = 'created_at'

    sort_column = last_login_subquery.c.last_login_at if sort_by == 'last_login_at' else getattr(Organization, sort_by)
    if sort_order.lower() == 'desc':
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    # Query for the total count
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Query for the paginated items
    result = await db.execute(query.order_by(sort_column).offset(offset).limit(per_page))
    organizations_with_login = result.all()

    return {
        "items": [
            {
                "id": org.Organization.id,
                "name": org.Organization.name,
                "slug": org.Organization.slug,
                "is_active": org.Organization.is_active,
                "created_at": org.Organization.created_at.isoformat(),
                "last_admin_login": org.last_login_at.isoformat() if org.last_login_at else None,
                "payment_status": "Unknown"  # Placeholder for actual payment status
            }
            for org in organizations_with_login
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/coupons", dependencies=[Depends(require_superadmin)])
async def list_coupons(
    db: AsyncSession = Depends(get_db), 
    page: int = 1, 
    per_page: int = 5,
    sort_by: str = 'created_at',
    sort_order: str = 'desc'
):
    """
    Lists all created coupons/vouchers for the superadmin.
    """
    offset = (page - 1) * per_page

    sortable_columns = {c.key for c in class_mapper(Coupon).columns}
    if sort_by not in sortable_columns:
        sort_by = 'created_at'

    sort_column = getattr(Coupon, sort_by)
    if sort_order.lower() == 'desc':
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    count_result = await db.execute(select(func.count(Coupon.id)))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Coupon)
        .order_by(sort_column)
        .offset(offset)
        .limit(per_page)
    )
    coupons = result.scalars().all()

    return {
        "items": coupons,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/charts/user-signups", dependencies=[Depends(require_superadmin)])
async def get_user_signups_chart_data(db: AsyncSession = Depends(get_db)):
    """
    Provides data for a chart visualizing user signups.
    Accepts optional `start_date` and `end_date` query parameters.
    """
    # This is a placeholder. In a real app, you'd parse these from request.query_params
    # and handle date validation carefully.
    # start_date_str = request.query_params.get('start_date')
    # end_date_str = request.query_params.get('end_date')

    result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count")
        )
        # Example of how to add date filtering:
        # .where(and_(User.created_at >= start_date, User.created_at <= end_date))
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    data = result.all()
    return [{"date": row.date.isoformat(), "count": row.count} for row in data]

@router.post("/coupons", status_code=201, dependencies=[Depends(require_superadmin)])
async def create_coupon(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Creates a new subscription voucher/coupon.
    """
    data = await request.json()
    new_coupon = Coupon(
        code=data['code'],
        description=data.get('description'),
        discount_type=data.get('discount_type', 'fixed'),
        value=data['value'],
        usage_limit=data.get('usage_limit', 1),
        is_active=True
    )
    db.add(new_coupon)
    await db.commit()
    await db.refresh(new_coupon)
    return new_coupon

@router.post("/coupons/{coupon_id}/toggle", dependencies=[Depends(require_superadmin)])
async def toggle_coupon_status(coupon_id: int, db: AsyncSession = Depends(get_db)):
    """
    Toggles the active status of a coupon.
    """
    coupon = await db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.is_active = not coupon.is_active
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon

@router.post("/organizations/{org_id}/toggle", dependencies=[Depends(require_superadmin)])
async def toggle_organization_status(org_id: int, db: AsyncSession = Depends(get_db)):
    """
    Toggles the active status of an organization.
    """
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.is_active = not org.is_active
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/settings", dependencies=[Depends(require_superadmin)])
async def get_system_settings():
    """
    Retrieves system-wide settings for the superadmin.
    """
    try:
        with open("system_settings.json", "r") as f:
            settings = json.load(f)
        return settings
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default settings if file is missing or corrupt
        return {
            "site_name": "Gaatha Suite",
            "maintenance_mode": False,
            "allow_new_registrations": True
        }

@router.post("/settings", dependencies=[Depends(require_superadmin)])
async def update_system_settings(request: Request):
    """
    Updates system-wide settings.
    """
    settings_data = await request.json()
    try:
        with open("system_settings.json", "w") as f:
            json.dump(settings_data, f, indent=4)
        return settings_data
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {e}")
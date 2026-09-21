from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crm import Organization
from app.models.user import User
from app.models.books import Account
from app.utils.dependencies import get_db
from app.schemas.auth import OnboardingCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/v2/auth", tags=["Onboarding"])

@router.post("/register")
async def onboard_organization(data: OnboardingCreate, db: AsyncSession = Depends(get_db)):
    """
    Atomic 'One-Click' registration. 
    Creates Org, User, and Default Accounts in one transaction.
    """
    try:
        async with db.begin():
            # 1. Create Organization
            new_org = Organization(
                name=data.org_name, 
                slug=data.org_name.lower().replace(" ", "-")
            )
            db.add(new_org)
            await db.flush() # Secure org.id for relation

            # 2. Create User
            hashed_password = pwd_context.hash(data.password)
            new_user = User(
                email=data.user_email, 
                username=data.user_email.split('@')[0],
                password_hash=hashed_password, 
                organization_id=new_org.id
            )
            db.add(new_user)

            # 3. Create Default Chart of Accounts
            coa = [
                Account(name="Cash", type="asset", code="1000", organization_id=new_org.id),
                Account(name="Sales Revenue", type="income", code="4000", organization_id=new_org.id),
                Account(name="Operating Expenses", type="expense", code="5000", organization_id=new_org.id)
            ]
            db.add_all(coa)
            
        return {"status": "success", "message": "Onboarding complete", "org_id": new_org.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
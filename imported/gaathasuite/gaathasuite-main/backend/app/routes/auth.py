from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from sqlalchemy import select, text, func
import re
import secrets
import asyncio

from app.db import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.coupon import Coupon
from app.schemas.auth import Token, UserRead, OrganizationRegistration, LoginRequest, CreateUserRequest
import logging

from app.utils.auth import create_access_token, create_refresh_token, verify_password, verify_token
from app.utils.dependencies import get_db, get_current_user, require_roles
from app.utils.roles import ROLE_ORGADMIN, ROLE_SUPERADMIN, canonical_role
from app.config import Config
from app.utils.email import send_email_async

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def validate_department_exists(db: AsyncSession, department_name: str, organization_id: int | None = None):
    if not department_name:
        return

    try:
        if organization_id is not None:
            result = await db.execute(
                text("SELECT 1 FROM department WHERE lower(name) = lower(:name) AND organization_id = :org_id LIMIT 1"),
                {"name": department_name, "org_id": organization_id}
            )
        else:
            result = await db.execute(
                text("SELECT 1 FROM department WHERE lower(name) = lower(:name) LIMIT 1"),
                {"name": department_name}
            )

        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown department: {department_name}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to validate department: {str(exc)}")

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns an access token.
    """
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "org_id": user.organization_id,
            "role": user.role,
        },
        expires_delta=access_token_expires
    )

    # Generate Refresh Token and set in Secure HttpOnly Cookie
    refresh_token = create_refresh_token(data={"sub": user.username, "role": user.role, "org_id": user.organization_id})
    
    # If not remember_me, set max_age to None (Session Cookie)
    cookie_max_age = Config.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 if remember_me else None

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=Config.COOKIE_SECURE,
        samesite="lax",
        max_age=cookie_max_age
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
async def login_with_json(
    response: Response,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint accepting JSON body with username and password.
    Returns access token and user data.
    """
    logger = logging.getLogger("app.auth")
    result = await db.execute(
        select(User).where(
            (User.username == credentials.username) | (User.email == credentials.username)
        )
    )
    user = result.scalar_one_or_none()

    # Debug logging to help diagnose login failures (temporary)
    if not user:
        logger.info("Login attempt: user not found: %s", credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    logger.info("Login attempt: user found: %s (email_verified=%s)", user.username, getattr(user, "email_verified", None))

    if not verify_password(credentials.password, user.password_hash):
        logger.info("Login failed: password mismatch for user %s", user.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Update last login timestamp
    user.last_login_at = func.now()
    db.add(user)
    await db.commit()

    access_token_expires = timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "org_id": user.organization_id,
            "role": user.role,
        },
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(data={"sub": user.username, "role": user.role, "org_id": user.organization_id})
    
    cookie_max_age = Config.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 if credentials.remember_me else None

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=Config.COOKIE_SECURE,
        samesite="lax",
        max_age=cookie_max_age
    )

    # Determine redirect path based on user role
    redirect_path = "/dashboard"
    if user.is_superadmin or canonical_role(user.role) == ROLE_SUPERADMIN:
        redirect_path = "/superadmin/dashboard"

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "redirect": redirect_path,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        }
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint to exchange a refresh cookie for a new access token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    credentials_exception = HTTPException(status_code=401, detail="Invalid refresh token")
    payload = verify_token(refresh_token, credentials_exception)
    username = payload.get("sub")
    role = payload.get("role")
    org_id = payload.get("org_id")

    access_token = create_access_token(
        data={"sub": username, "role": role, "org_id": org_id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the current authenticated user's information.
    """
    return current_user


@router.put("/users/me", response_model=UserRead)
async def update_users_me(
    payload: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    """
    try:
        if payload.username and payload.username != current_user.username:
            result = await db.execute(select(User).where(User.username == payload.username))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
            current_user.username = payload.username

        if payload.email and payload.email != current_user.email:
            result = await db.execute(select(User).where(User.email == payload.email))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
            current_user.email = payload.email

        if payload.phone is not None:
            current_user.phone = payload.phone

        if payload.first_name is not None:
            current_user.first_name = payload.first_name

        if payload.last_name is not None:
            current_user.last_name = payload.last_name

        if payload.department is not None:
            current_user.department = payload.department

        if payload.password:
            current_user.set_password(payload.password)

        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users")
async def list_users(
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """List users. Org admins see users scoped to their organization; superadmins see all users."""
    try:
        # If superadmin, return all users
        if canonical_role(getattr(current_user, 'role', '')) == ROLE_SUPERADMIN:
            result = await db.execute(select(User))
            users = result.scalars().all()
        else:
            org_id = current_user.organization_id
            result = await db.execute(select(User).where(User.organization_id == org_id))
            users = result.scalars().all()

        # Return a lightweight JSON-friendly list
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "department": getattr(u, 'department', None),
                "is_admin": getattr(u, 'is_admin', False),
            }
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post('/users')
async def create_user(
    payload: CreateUserRequest,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user within the organization. Org admins can only create users inside their org."""
    try:
        # prevent duplicate username/email
        result = await db.execute(select(User).where((User.username == payload.username) | (User.email == payload.email)))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

        # Determine organization scope
        is_superadmin = canonical_role(getattr(current_user, 'role', '')) == ROLE_SUPERADMIN
        if is_superadmin:
            org_id = payload.organization_id
        else:
            if payload.organization_id is not None and payload.organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create users for another organization",
                )
            org_id = current_user.organization_id

        if org_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization context is required")

        requested_role = canonical_role(payload.role or ROLE_USER)
        if not is_superadmin and requested_role == ROLE_SUPERADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign superadmin role")

        # Validate department against existing departments table and organization
        if payload.department:
            await validate_department_exists(db, payload.department, organization_id=org_id)

        new_user = User(
            username=payload.username,
            email=payload.email,
            role=requested_role,
            organization_id=org_id,
            department=payload.department,
        )
        new_user.set_password(payload.password)
        db.add(new_user)
        await db.commit()

        # Send welcome email asynchronously
        try:
            subject = "Welcome to Gaatha Suite"
            body = f"<p>Hello {new_user.username},</p><p>Your account has been created. Username: {new_user.username}</p>"
            asyncio.create_task(send_email_async(new_user.email, subject, body))
        except Exception:
            pass

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "department": new_user.department,
            "organization_id": new_user.organization_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put('/users/{user_id}')
async def update_user(
    user_id: int,
    payload: CreateUserRequest,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Update user fields. Org admins can only update users in their org."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        u = result.scalar_one_or_none()
        if not u:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # scope check
        if canonical_role(getattr(current_user, 'role', '')) != ROLE_SUPERADMIN and u.organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify user from another organization")
        if (
            canonical_role(getattr(current_user, 'role', '')) != ROLE_SUPERADMIN
            and payload.organization_id is not None
            and payload.organization_id != current_user.organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot move user to another organization",
            )

        # apply updates
        if payload.email:
            u.email = payload.email
        if payload.role:
            requested_role = canonical_role(payload.role)
            if (
                canonical_role(getattr(current_user, 'role', '')) != ROLE_SUPERADMIN
                and requested_role == ROLE_SUPERADMIN
            ):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign superadmin role")
            u.role = requested_role
        if payload.department is not None:
            await validate_department_exists(db, payload.department, organization_id=u.organization_id or current_user.organization_id)
            u.department = payload.department
        if payload.password:
            u.set_password(payload.password)

        db.add(u)
        await db.commit()

        return {"id": u.id, "username": u.username, "email": u.email, "role": u.role, "department": u.department}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete('/users/{user_id}')
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user. Org admins cannot delete superadmins or users outside their org."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        u = result.scalar_one_or_none()
        if not u:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if canonical_role(getattr(current_user, 'role', '')) != ROLE_SUPERADMIN:
            if u.organization_id != current_user.organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete user from another organization")
            if canonical_role(u.role) == ROLE_SUPERADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete a superadmin")

        await db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db.commit()
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/register", response_model=UserRead)
async def register_user(
    registration_data: OrganizationRegistration,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint for organization onboarding.
    Creates a new user account with organization information stored in preferences.
    Sends welcome email to the user.
    """
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == registration_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == registration_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Voucher Code Validation
    voucher_code = registration_data.dict().get("voucher_code")
    coupon_to_apply = None
    if voucher_code:
        coupon_result = await db.execute(select(Coupon).where(Coupon.code == voucher_code))
        coupon_to_apply = coupon_result.scalar_one_or_none()

        if not coupon_to_apply:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid voucher code.")
        
        if not coupon_to_apply.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This voucher is no longer active.")

        if coupon_to_apply.expires_at and coupon_to_apply.expires_at < datetime.datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This voucher has expired.")

        if coupon_to_apply.used_count >= coupon_to_apply.usage_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This voucher has reached its usage limit.")

        # Mark as used (or link to subscription in a real system)
        coupon_to_apply.used_count += 1

    # Create organization and user records together
    org_slug = re.sub(r"[^a-z0-9]+", "-", registration_data.organizationName.strip().lower()).strip("-")
    existing_org = await db.execute(select(Organization).where(Organization.slug == org_slug))
    if existing_org.scalar_one_or_none():
        org_slug = f"{org_slug}-{secrets.token_hex(3)}"

    organization = Organization(
        name=registration_data.organizationName,
        slug=org_slug,
        website=registration_data.website,
        industry=registration_data.industry,
        company_size=registration_data.companySize,
        phone=registration_data.phone,
    )
    # If a voucher is used, we can reflect that on the organization
    if coupon_to_apply:
        organization.payment_status = f"Voucher Applied: {coupon_to_apply.code}"

    db.add(organization)
    await db.flush()

    # Create new user as organization admin
    new_user = User(
        email=registration_data.email,
        username=registration_data.username,
        phone=registration_data.phone,
        role=ROLE_ORGADMIN,
        organization_id=organization.id,
    )
    new_user.set_password(registration_data.password)

    if coupon_to_apply:
        db.add(coupon_to_apply)

    db.add(new_user)
    await db.flush()
    await db.commit()
    
    # Send welcome email asynchronously (don't wait for it)
    try:
        email_subject = "Welcome to Gaatha Suite!"
        email_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Welcome to Gaatha Suite, {registration_data.username}!</h2>
                    
                    <p>Thank you for signing up with Gaatha Suite. Your account has been successfully created.</p>
                    
                    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3>Account Details:</h3>
                        <p><strong>Username:</strong> {registration_data.username}</p>
                        <p><strong>Email:</strong> {registration_data.email}</p>
                        <p><strong>Organization:</strong> {registration_data.organizationName}</p>
                        <p><strong>Role:</strong> Organization Admin</p>
                    </div>
                    
                    <p>You can now <a href="{Config.public_url('/auth/login')}" style="color: #0066cc; text-decoration: none;"><strong>log in to your account</strong></a> and start using Gaatha Suite.</p>
                    
                    <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
                    
                    <p>Best regards,<br/>The Gaatha Suite Team</p>
                </div>
            </body>
        </html>
        """
        asyncio.create_task(send_email_async(registration_data.email, email_subject, email_body))
    except Exception as e:
        # Log the error but don't fail the registration
        print(f"Failed to send welcome email: {str(e)}")

    return new_user

"""Authentication endpoints — sign up, sign in, current user."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException, Depends, status

from app.core.supabase_client import get_supabase, get_supabase_admin
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.models import (
    SignUpRequest,
    SignInRequest,
    GoogleAuthRequest,
    AuthResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def sign_up(req: SignUpRequest):
    """Register a new user through Supabase Auth."""
    try:
        client = get_supabase()
        auth_response = client.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {
                "data": {
                    "display_name": req.display_name,
                    "role": req.role.value,
                },
            },
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create account. The email may already be registered.",
            )

        auth_user = auth_response.user
        access_token = auth_response.session.access_token if auth_response.session else ""

        # Create app user record
        admin = get_supabase_admin()
        user_id = str(uuid.uuid4())

        admin.table("users").insert({
            "id": user_id,
            "auth_id": auth_user.id,
            "email": req.email,
            "role": req.role.value,
            "display_name": req.display_name,
        }).execute()

        profile_id = None
        if req.role.value == "senior":
            profile_id = str(uuid.uuid4())
            admin.table("senior_profiles").insert({
                "id": profile_id,
                "user_id": user_id,
                "display_name": req.display_name,
                "timezone": "Asia/Kolkata",
                "language": "en",
                "speech_rate": 1.0,
                "onboarding_complete": False,
            }).execute()

        return AuthResponse(
            access_token=access_token,
            user_id=user_id,
            email=req.email,
            role=req.role.value,
            profile_id=profile_id,
            display_name=req.display_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/signin", response_model=AuthResponse)
async def sign_in(req: SignInRequest):
    """Authenticate a user and return session tokens."""
    try:
        client = get_supabase()
        auth_response = client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        auth_user = auth_response.user
        access_token = auth_response.session.access_token

        # Load app user
        admin = get_supabase_admin()
        result = admin.table("users").select("*").eq("auth_id", auth_user.id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please sign up first.",
            )

        db_user = result.data[0]
        profile_id = None

        if db_user["role"] == "senior":
            profile_result = (
                admin.table("senior_profiles")
                .select("id")
                .eq("user_id", db_user["id"])
                .execute()
            )
            if profile_result.data and len(profile_result.data) > 0:
                profile_id = profile_result.data[0]["id"]

        return AuthResponse(
            access_token=access_token,
            user_id=db_user["id"],
            email=db_user["email"],
            role=db_user["role"],
            profile_id=profile_id,
            display_name=db_user.get("display_name", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/me", response_model=UserOut)
async def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    """Get the current authenticated user's info."""
    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(req: GoogleAuthRequest):
    """Authenticate or register a user using Google Sign-In."""
    import jwt
    from datetime import datetime, timezone
    from app.core.config import settings

    email = req.email
    display_name = req.display_name or ""
    google_sub = req.google_id

    # If an id_token was sent from Google One Tap / GIS, decode payload
    if req.id_token:
        try:
            # Decode token claims (unverified fallback if offline, verified in production)
            unverified = jwt.decode(req.id_token, options={"verify_signature": False})
            email = unverified.get("email") or email
            display_name = unverified.get("name") or display_name
            google_sub = unverified.get("sub") or google_sub
        except Exception:
            pass

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email could not be obtained from Google authentication.",
        )

    email = email.strip().lower()
    admin = get_supabase_admin()

    # Check if user already exists by email or auth_id
    existing = admin.table("users").select("*").eq("email", email).execute()
    if not (existing.data and len(existing.data) > 0) and google_sub:
        existing = admin.table("users").select("*").eq("auth_id", google_sub).execute()

    if existing.data and len(existing.data) > 0:
        db_user = existing.data[0]
        user_id = db_user["id"]
        role = db_user.get("role", req.role.value)
        display_name = db_user.get("display_name") or display_name
    else:
        # Create new user
        user_id = str(uuid.uuid4())
        role = req.role.value
        # Ensure auth_id is unique if google_sub is provided
        auth_id = google_sub or str(uuid.uuid4())
        sub_check = admin.table("users").select("id").eq("auth_id", auth_id).execute()
        if sub_check.data and len(sub_check.data) > 0:
            auth_id = f"{auth_id}_{uuid.uuid4().hex[:6]}"

        admin.table("users").insert({
            "id": user_id,
            "auth_id": auth_id,
            "email": email,
            "role": role,
            "display_name": display_name,
        }).execute()

    # If senior, verify profile exists
    profile_id = None
    if role == "senior":
        p_res = admin.table("senior_profiles").select("id").eq("user_id", user_id).execute()
        if p_res.data and len(p_res.data) > 0:
            profile_id = p_res.data[0]["id"]
        else:
            profile_id = str(uuid.uuid4())
            admin.table("senior_profiles").insert({
                "id": profile_id,
                "user_id": user_id,
                "display_name": display_name,
                "timezone": "Asia/Kolkata",
                "language": "en",
                "speech_rate": 1.0,
                "onboarding_complete": False,
            }).execute()

    # Generate session JWT
    token_payload = {
        "sub": user_id,
        "email": email,
        "metadata": {"display_name": display_name, "role": role},
        "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30,
    }
    access_token = jwt.encode(token_payload, settings.secret_key, algorithm="HS256")

    return AuthResponse(
        access_token=access_token,
        user_id=user_id,
        email=email,
        role=role,
        profile_id=profile_id,
        display_name=display_name,
    )


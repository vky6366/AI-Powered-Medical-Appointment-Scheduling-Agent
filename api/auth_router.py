from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agents.auth import (
    verify_google_token,
    create_access_token,
)

from agents.db import SessionLocal

from agents.db_service import (
    get_user_by_google_id,
    create_google_user,
    get_user_by_id,
    get_patient_profile,
    create_patient_profile,
)

from api.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class GoogleAuthRequest(BaseModel):
    token: str


@router.post("/google")
async def google_auth(
    body: GoogleAuthRequest,
):
    """
    Exchange a Google ID token for an internal JWT.

    Flow:
      1. Verify the Google ID token with google-auth library.
      2. Look up the user by google_id; create if new.
      3. Reject inactive accounts.
      4. Stamp last_login.
      5. Return a signed JWT + user profile.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # Verify Google token
        # --------------------------------------------------

        user_info = verify_google_token(body.token)

        # --------------------------------------------------
        # Find or create user
        # --------------------------------------------------

        user = get_user_by_google_id(
            db,
            user_info["google_id"],
        )

        if not user:
            user = create_google_user(
                db=db,
                google_id=user_info["google_id"],
                name=user_info["name"] or user_info["email"].split("@")[0],
                email=user_info["email"],
                profile_picture=user_info.get("picture"),
            )

        # --------------------------------------------------
        # Reject deactivated accounts
        # --------------------------------------------------

        if hasattr(user, "is_active") and user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )

        # --------------------------------------------------
        # Stamp last_login
        # --------------------------------------------------

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        # --------------------------------------------------
        # Issue JWT
        # --------------------------------------------------

        access_token = create_access_token(user.id)

        # --------------------------------------------------
        # Check profile completeness
        # --------------------------------------------------
        # Phone is compulsory. Insurance/DOB are optional.
        profile_complete = bool(user.phone)

        return {
            "access_token": access_token,
            "profile_complete": profile_complete,
            "user": {
                "id":              user.id,
                "name":            user.name,
                "email":           user.email,
                "profile_picture": user.profile_picture,
                "last_login":      user.last_login.isoformat()
                                   if user.last_login else None,
            },
        }

    finally:

        db.close()

from typing import Optional

class ProfileCompleteRequest(BaseModel):
    phone: str
    dob: Optional[str] = None
    insurance_carrier: Optional[str] = None
    insurance_member_id: Optional[str] = None
    insurance_group: Optional[str] = None

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

@router.post("/complete-profile")
async def complete_profile(
    body: ProfileCompleteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Complete the user's profile with additional details like phone,
    DOB, and insurance information.
    """
    db = SessionLocal()
    try:
        user_id = current_user["user_id"]
        user = get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
            
        # Update user's phone
        user.phone = body.phone
        
        # Parse DOB if provided
        dob_date = None
        if body.dob and body.dob.strip():
            try:
                dob_date = datetime.strptime(body.dob.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for dob '{body.dob}'. Please use YYYY-MM-DD."
                )
            
        # Check if patient profile exists, update or create
        profile = get_patient_profile(db, user_id)
        if profile:
            profile.dob = dob_date
            profile.insurance_carrier = body.insurance_carrier
            profile.insurance_member_id = body.insurance_member_id
            profile.insurance_group = body.insurance_group
        else:
            profile = create_patient_profile(
                db=db,
                user_id=user_id,
                dob=dob_date,
                insurance_carrier=body.insurance_carrier,
                insurance_member_id=body.insurance_member_id,
                insurance_group=body.insurance_group,
            )
            
        db.commit()
        db.refresh(user)
        
        return {"status": "success", "message": "Profile completed successfully."}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number is already registered to another account. Please use a different phone number."
        )
    finally:
        db.close()
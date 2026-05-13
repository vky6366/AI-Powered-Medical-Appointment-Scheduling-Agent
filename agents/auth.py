from __future__ import annotations

import os
import jwt

from datetime import (
    datetime,
    timedelta,
)

import firebase_admin

from firebase_admin import (
    credentials,
    auth as firebase_auth,
)
# =====================================================
# FIREBASE INIT
# =====================================================


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

firebase_path = (
    BASE_DIR
    / "medical-appointment-85be7-firebase-adminsdk-fbsvc-e32efcc4d8.json"
)

if not firebase_admin._apps:

    cred = credentials.Certificate(
        str(firebase_path)
    )

    firebase_admin.initialize_app(cred)

# =====================================================
# JWT CONFIG
# =====================================================

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "super-secret-key",
)

JWT_ALGORITHM = "HS256"

# =====================================================
# VERIFY FIREBASE TOKEN
# =====================================================

def verify_google_token(
    token: str,
):

    decoded_token = firebase_auth.verify_id_token(
        token
    )

    return {
        "google_id": decoded_token["uid"],

        "email": decoded_token.get(
            "email"
        ),

        "name": decoded_token.get(
            "name",
            ""
        ),

        "picture": decoded_token.get(
            "picture",
            ""
        ),
    }

# =====================================================
# CREATE APP JWT
# =====================================================

def create_access_token(
    user_id: int,
):

    payload = {
        "user_id": user_id,

        "exp": (
            datetime.utcnow()
            + timedelta(days=7)
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

# =====================================================
# VERIFY APP JWT
# =====================================================

def verify_access_token(
    token: str,
):

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )
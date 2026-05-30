import os

from models import (
    NaukriSession,
    SessionLocal
)

def get_or_create_profile(user_id):

    db = SessionLocal()

    try:

        session = db.query(
            NaukriSession
        ).filter(
            NaukriSession.user_id == user_id
        ).first()

        if session:
            return session.profile_path

        profile_path = (
            f"naukri_profiles/user_{user_id}"
        )

        os.makedirs(
            profile_path,
            exist_ok=True
        )

        new_session = NaukriSession(
            user_id=user_id,
            profile_path=profile_path,
            status="active"
        )

        db.add(new_session)
        db.commit()

        return profile_path

    finally:
        db.close()


def get_profile_path(user_id):

    db = SessionLocal()

    try:

        session = db.query(
            NaukriSession
        ).filter(
            NaukriSession.user_id == user_id
        ).first()

        if not session:
            return None

        return session.profile_path

    finally:
        db.close()
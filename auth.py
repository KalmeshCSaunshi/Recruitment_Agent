from models import User, SessionLocal
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

bcrypt = Bcrypt()

def register_user(name, email, password):

    db = SessionLocal()

    try:

        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            return {
                "success": False,
                "message": "Email already exists"
            }

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        user = User(
            name=name,
            email=email,
            password_hash=hashed_password
        )

        db.add(user)
        db.commit()

        return {
            "success": True,
            "message": "User registered successfully"
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


def login_user(email, password):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            return {
                "success": False,
                "message": "Invalid Email"
            }

        if not bcrypt.check_password_hash(
            user.password_hash,
            password
        ):
            return {
                "success": False,
                "message": "Invalid Password"
            }

        token = create_access_token(
            identity=str(user.id)
        )

        return {
            "success": True,
            "token": token,
            "user_id": user.id,
            "name": user.name
        }

    finally:
        db.close()
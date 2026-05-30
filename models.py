from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime
)
from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://recruitment_user:Recruit%40123@localhost:5432/recruitment_agent"

engine = create_engine(DATABASE_URL)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)


class NaukriSession(Base):
    __tablename__ = "naukri_sessions"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        nullable=False,
        unique=True
    )

    profile_path = Column(
        String(500),
        nullable=False
    )

    naukri_email = Column(
        String(255)
    )

    status = Column(
        String(50),
        default="active"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

print("✅ Users table created")
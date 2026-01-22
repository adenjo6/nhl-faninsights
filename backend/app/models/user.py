from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    # Clerk user ID (format: user_xxxxxxxxxxxxx)
    clerk_id = Column(String, primary_key=True, index=True)

    # User info synced from Clerk
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)

    # Role management
    role = Column(String, nullable=False, default="user")  # user, moderator, admin

    # Status
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
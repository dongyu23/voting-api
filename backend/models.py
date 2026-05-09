from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    creator_id = Column(Integer, nullable=False)
    expires_at = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, nullable=False, index=True)
    text = Column(String(200), nullable=False)


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("poll_id", "user_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, nullable=False, index=True)
    option_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())

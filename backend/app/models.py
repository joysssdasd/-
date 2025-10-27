from __future__ import annotations

import enum
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import get_settings
from .database import Base

settings = get_settings()


class UserStatus(enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class PostStatus(enum.Enum):
    PUBLISHED = "published"
    UNLISTED = "unlisted"
    EXPIRED = "expired"


class PointChangeType(enum.Enum):
    RECHARGE = "recharge"
    PUBLISH = "publish"
    VIEW_CONTACT = "view_contact"
    REWARD = "reward"
    REFUND = "refund"


class SMSCode(Base):
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(11), index=True)
    code: Mapped[str] = mapped_column(String(6))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    wechat_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    invite_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=True, index=True)
    invited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=settings.registration_bonus)
    total_posts: Mapped[int] = mapped_column(Integer, default=0)
    total_deals: Mapped[int] = mapped_column(Integer, default=0)
    deal_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invited_users: Mapped[list["User"]] = relationship(
        "User", backref="inviter", remote_side=[id]
    )
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="owner")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    trade_type: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    extra_info: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    view_limit: Mapped[int] = mapped_column(Integer, default=settings.post_default_view_quota)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    deal_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), default=PostStatus.PUBLISHED, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[User] = relationship("User", back_populates="posts")
    contact_views: Mapped[list["ContactView"]] = relationship("ContactView", back_populates="post")

    def is_active(self) -> bool:
        return self.status == PostStatus.PUBLISHED and self.expire_at > datetime.utcnow()


class ContactView(Base):
    __tablename__ = "contact_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True, nullable=False)
    viewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    has_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deal: Mapped[bool] = mapped_column(Boolean, default=False)

    post: Mapped[Post] = relationship("Post", back_populates="contact_views")
    viewer: Mapped[User] = relationship("User")


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    change_type: Mapped[PointChangeType] = mapped_column(Enum(PointChangeType), nullable=False)
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    related_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User")


class InviteRecord(Base):
    __tablename__ = "invite_records"
    __table_args__ = (UniqueConstraint("inviter_id", "invitee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    inviter: Mapped[User] = relationship("User", foreign_keys=[inviter_id], backref="invite_records")
    invitee: Mapped[User] = relationship("User", foreign_keys=[invitee_id])


def compute_expire_at() -> datetime:
    return datetime.utcnow() + timedelta(hours=settings.post_valid_hours)

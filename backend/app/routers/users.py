from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import InviteRecord, Post, PostStatus, User
from ..schemas import DashboardResponse, InviteRecordResponse, UserBase

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserBase)
def get_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    active_posts = (
        db.query(Post)
        .filter(Post.user_id == current_user.id, Post.status == PostStatus.PUBLISHED)
        .count()
    )
    return DashboardResponse(
        points=current_user.points,
        deal_rate=float(current_user.deal_rate or 0),
        total_posts=current_user.total_posts,
        active_posts=active_posts,
    )


@router.get("/invites", response_model=list[InviteRecordResponse])
def list_invites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InviteRecord]:
    records = (
        db.query(InviteRecord)
        .filter(InviteRecord.inviter_id == current_user.id)
        .order_by(InviteRecord.created_at.desc())
        .all()
    )
    return records

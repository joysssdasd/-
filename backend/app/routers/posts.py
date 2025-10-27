from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import (
    ContactView,
    InviteRecord,
    PointChangeType,
    Post,
    PostStatus,
    User,
)
from ..schemas import (
    ContactViewResponse,
    DealConfirmationRequest,
    Pagination,
    PostCreateRequest,
    PostDetail,
    PostListItem,
    PostStatusUpdate,
)
from ..utils import apply_point_change, update_user_deal_rate

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])
settings = get_settings()


def refresh_post_status(db: Session, post: Post) -> None:
    if post.status == PostStatus.PUBLISHED and post.expire_at <= datetime.utcnow():
        remaining = max(post.view_limit - post.view_count, 0)
        post.status = PostStatus.EXPIRED
        if remaining > 0:
            apply_point_change(
                db,
                post.owner,
                PointChangeType.REFUND,
                remaining,
                description=f"Post {post.id} expired, refund {remaining} points",
                related_id=post.id,
            )
        db.add(post)
        db.commit()


def reward_invite_if_applicable(db: Session, user: User) -> None:
    record = (
        db.query(InviteRecord)
        .filter(InviteRecord.invitee_id == user.id, InviteRecord.reward_granted.is_(False))
        .first()
    )
    if not record:
        return

    inviter = db.query(User).filter(User.id == record.inviter_id).with_for_update().first()
    if not inviter:
        return

    apply_point_change(
        db,
        inviter,
        PointChangeType.REWARD,
        settings.invite_reward_inviter,
        description=f"Invite reward for user {user.phone}",
        related_id=user.id,
    )
    apply_point_change(
        db,
        user,
        PointChangeType.REWARD,
        settings.invite_reward_invitee,
        description="Invitee first post reward",
        related_id=user.id,
    )
    record.reward_granted = True
    db.add(record)
    db.commit()


@router.post("", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Post:
    user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
    if user.points < settings.post_publish_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient points")

    post = Post(
        user_id=user.id,
        title=payload.title,
        keywords=payload.keywords,
        price=payload.price,
        trade_type=payload.trade_type,
        delivery_date=payload.delivery_date,
        extra_info=payload.extra_info,
        view_limit=settings.post_default_view_quota,
        expire_at=datetime.utcnow() + timedelta(hours=settings.post_valid_hours),
    )
    db.add(post)

    apply_point_change(
        db,
        user,
        PointChangeType.PUBLISH,
        -settings.post_publish_cost,
        description="Publish post",
    )

    user.total_posts += 1
    update_user_deal_rate(user)
    db.add(user)
    db.commit()
    db.refresh(post)

    if user.total_posts == 1:
        reward_invite_if_applicable(db, user)

    return post


@router.get("", response_model=Pagination)
def list_posts(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    trade_type: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: Optional[str] = Query("deal_rate"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Pagination:
    query = db.query(Post).options(selectinload(Post.owner)).join(User).filter(Post.status == PostStatus.PUBLISHED)

    now = datetime.utcnow()
    query = query.filter(Post.expire_at > now)

    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(or_(Post.title.ilike(like_pattern), Post.keywords.ilike(like_pattern)))

    if trade_type:
        query = query.filter(Post.trade_type == trade_type)

    if min_price is not None:
        query = query.filter(Post.price >= min_price)
    if max_price is not None:
        query = query.filter(Post.price <= max_price)

    if sort_by == "created_at":
        query = query.order_by(Post.created_at.desc())
    else:
        query = query.order_by(User.deal_rate.desc(), Post.created_at.desc(), (Post.view_limit - Post.view_count).desc())

    total = query.count()
    posts = query.offset(offset).limit(limit).all()

    for post in posts:
        refresh_post_status(db, post)

    items = [PostListItem.from_orm(post) for post in posts]
    return Pagination(total=total, items=items)


@router.get("/{post_id}", response_model=PostDetail)
def get_post(post_id: int, db: Session = Depends(get_db)) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    refresh_post_status(db, post)

    return post


@router.put("/{post_id}/status", response_model=PostDetail)
def update_post_status(
    post_id: int,
    payload: PostStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Post:
    status_value = payload.status
    post = (
        db.query(Post)
        .filter(Post.id == post_id, Post.user_id == current_user.id)
        .with_for_update()
        .first()
    )
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if status_value not in {PostStatus.UNLISTED, PostStatus.PUBLISHED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status change")

    if status_value == PostStatus.UNLISTED and post.status == PostStatus.PUBLISHED:
        remaining = max(post.view_limit - post.view_count, 0)
        if remaining > 0:
            apply_point_change(
                db,
                post.owner,
                PointChangeType.REFUND,
                remaining,
                description="Manual unlist refund",
                related_id=post.id,
            )
        post.status = PostStatus.UNLISTED
    elif status_value == PostStatus.PUBLISHED and post.status != PostStatus.PUBLISHED:
        if post.owner.points < settings.post_publish_cost:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient points")
        apply_point_change(
            db,
            post.owner,
            PointChangeType.PUBLISH,
            -settings.post_publish_cost,
            description="Re-publish post",
            related_id=post.id,
        )
        post.status = PostStatus.PUBLISHED
        post.view_count = 0
        post.view_limit = settings.post_default_view_quota
        post.expire_at = datetime.utcnow() + timedelta(hours=settings.post_valid_hours)

    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/contact", response_model=ContactViewResponse)
def view_contact(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContactView:
    post = db.query(Post).filter(Post.id == post_id).with_for_update().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    refresh_post_status(db, post)
    if post.status != PostStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post not available")

    existing_view = (
        db.query(ContactView)
        .filter(ContactView.post_id == post_id, ContactView.viewer_id == current_user.id)
        .first()
    )
    if existing_view:
        return existing_view

    if post.view_count >= post.view_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="View limit reached")

    viewer = db.query(User).filter(User.id == current_user.id).with_for_update().first()
    if viewer.points < settings.contact_view_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient points")

    apply_point_change(
        db,
        viewer,
        PointChangeType.VIEW_CONTACT,
        -settings.contact_view_cost,
        description=f"View contact for post {post.id}",
        related_id=post.id,
    )

    contact_view = ContactView(post_id=post.id, viewer_id=viewer.id)
    post.view_count += 1
    db.add(contact_view)
    db.add(post)
    db.commit()
    db.refresh(contact_view)
    return contact_view


@router.post("/{post_id}/contact/{contact_id}/confirm", response_model=ContactViewResponse)
def confirm_deal(
    post_id: int,
    contact_id: int,
    payload: DealConfirmationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContactView:
    contact_view = (
        db.query(ContactView)
        .join(Post)
        .filter(
            ContactView.id == contact_id,
            ContactView.post_id == post_id,
            ContactView.viewer_id == current_user.id,
        )
        .with_for_update()
        .first()
    )
    if not contact_view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact view not found")

    if contact_view.has_confirmed:
        return contact_view

    contact_view.has_confirmed = True
    contact_view.is_deal = payload.is_deal

    if payload.is_deal:
        post = db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if post:
            post.deal_count += 1
            owner = db.query(User).filter(User.id == post.user_id).with_for_update().first()
            if owner:
                owner.total_deals += 1
                update_user_deal_rate(owner)
                db.add(owner)
            db.add(post)

    db.add(contact_view)
    db.commit()
    db.refresh(contact_view)
    return contact_view

import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .config import get_settings
from .models import PointChangeType, PointTransaction, User

settings = get_settings()


def generate_sms_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def generate_invite_code(session: Session) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not session.query(User).filter(User.invite_code == code).first():
            return code


def apply_point_change(
    session: Session,
    user: User,
    change_type: PointChangeType,
    amount: int,
    description: str,
    related_id: int | None = None,
) -> None:
    user.points += amount
    if user.points < 0:
        raise ValueError("Insufficient points")

    transaction = PointTransaction(
        user_id=user.id,
        change_type=change_type,
        change_amount=amount,
        balance_after=user.points,
        description=description,
        related_id=related_id,
    )
    session.add(transaction)


def update_user_deal_rate(user: User) -> None:
    if user.total_posts == 0:
        user.deal_rate = 0
    else:
        user.deal_rate = round(user.total_deals * 100 / user.total_posts, 1)

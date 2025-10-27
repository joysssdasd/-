from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import PointTransaction, User
from ..schemas import PointTransactionResponse

router = APIRouter(prefix="/api/v1/points", tags=["points"])


@router.get("/balance")
def get_balance(current_user: User = Depends(get_current_user)) -> dict[str, int]:
    return {"points": current_user.points}


@router.get("/transactions", response_model=list[PointTransactionResponse])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PointTransaction]:
    transactions = (
        db.query(PointTransaction)
        .filter(PointTransaction.user_id == current_user.id)
        .order_by(PointTransaction.created_at.desc())
        .all()
    )
    return transactions

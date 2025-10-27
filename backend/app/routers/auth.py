from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import InviteRecord, SMSCode, User
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    RequestSMSCode,
    TokenResponse,
)
from ..security import create_access_token
from ..utils import generate_invite_code, generate_sms_code

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def validate_sms_code(session: Session, phone: str, code: str) -> SMSCode:
    sms_code = (
        session.query(SMSCode)
        .filter(SMSCode.phone == phone, SMSCode.is_valid.is_(True))
        .order_by(SMSCode.created_at.desc())
        .first()
    )
    if not sms_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code required")

    if sms_code.locked_until and sms_code.locked_until > datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Too many attempts, try later")

    if sms_code.expires_at < datetime.utcnow():
        sms_code.is_valid = False
        session.add(sms_code)
        session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

    if sms_code.code != code:
        sms_code.attempts += 1
        if sms_code.attempts >= settings.sms_max_attempts:
            sms_code.locked_until = datetime.utcnow() + timedelta(minutes=settings.sms_attempt_lock_minutes)
        session.add(sms_code)
        session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    sms_code.is_valid = False
    session.add(sms_code)
    session.commit()
    return sms_code


@router.post("/request-code")
def request_sms_code(payload: RequestSMSCode, db: Session = Depends(get_db)) -> dict[str, str]:
    code = generate_sms_code()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.sms_code_expire_minutes)

    sms_code = SMSCode(
        phone=payload.phone,
        code=code,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
    )
    db.add(sms_code)
    db.commit()

    # In production, integrate with SMS provider. For MVP we return the code for testing.
    return {"message": "Verification code generated", "code": code}


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    validate_sms_code(db, payload.phone, payload.code)

    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")

    if db.query(User).filter(User.wechat_id == payload.wechat_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WeChat already registered")

    invited_by_id = None
    if payload.invite_code:
        inviter = db.query(User).filter(User.invite_code == payload.invite_code).first()
        if not inviter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite code invalid")
        invited_by_id = inviter.id

    new_user = User(
        phone=payload.phone,
        wechat_id=payload.wechat_id,
        invite_code=generate_invite_code(db),
        invited_by_id=invited_by_id,
        points=settings.registration_bonus,
    )
    db.add(new_user)
    db.flush()

    if invited_by_id:
        invite_record = InviteRecord(inviter_id=invited_by_id, invitee_id=new_user.id)
        db.add(invite_record)

    db.commit()
    token = create_access_token(str(new_user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    validate_sms_code(db, payload.phone, payload.code)

    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)

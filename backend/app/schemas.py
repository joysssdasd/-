from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional

from decimal import Decimal

from pydantic import BaseModel, Field, constr, root_validator

from .models import PointChangeType, PostStatus, UserStatus


PhoneNumber = constr(pattern=r"^\d{11}$")
WeChatId = constr(pattern=r"^[A-Za-z0-9_\-]{6,20}$")
InviteCode = constr(pattern=r"^[A-Za-z0-9]{4,10}$")
SMSCode = constr(pattern=r"^\d{6}$")


class ORMModel(BaseModel):
    class Config:
        orm_mode = True
        json_encoders = {Decimal: float}


class TokenResponse(ORMModel):
    access_token: str
    token_type: str = "bearer"


class RequestSMSCode(BaseModel):
    phone: PhoneNumber


class VerifySMSCode(BaseModel):
    phone: PhoneNumber
    code: SMSCode


class RegisterRequest(VerifySMSCode):
    wechat_id: WeChatId
    invite_code: Optional[InviteCode] = None


class LoginRequest(VerifySMSCode):
    pass


class UserBase(ORMModel):
    id: int
    phone: str
    wechat_id: str
    invite_code: Optional[str]
    invited_by_id: Optional[int]
    points: int
    total_posts: int
    total_deals: int
    deal_rate: float = Field(..., description="Percentage of deals")
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserSummary(ORMModel):
    id: int
    phone: str
    wechat_id: str
    deal_rate: float

    class Config:
        orm_mode = True


class PointTransactionResponse(ORMModel):
    id: int
    change_type: PointChangeType
    change_amount: int
    balance_after: int
    related_id: Optional[int]
    description: str
    created_at: datetime

    class Config:
        orm_mode = True


class PostBase(ORMModel):
    id: int
    title: str
    keywords: str
    price: float
    trade_type: int
    delivery_date: Optional[date]
    extra_info: Optional[str]
    view_limit: int
    view_count: int
    deal_count: int
    status: PostStatus
    expire_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PostListItem(PostBase):
    owner: UserSummary


class PostCreateRequest(BaseModel):
    title: constr(max_length=30)
    keywords: constr(max_length=200)
    price: float = Field(ge=0)
    trade_type: int
    delivery_date: Optional[date] = None
    extra_info: Optional[constr(max_length=100)] = None

    @root_validator
    def check_trade_fields(cls, values):
        trade_type = values.get('trade_type')
        if trade_type in {3, 4}:
            if values.get('delivery_date') is None:
                raise ValueError('delivery_date is required for trade_type 3 or 4')
            if values.get('extra_info') is None:
                raise ValueError('extra_info is required for trade_type 3 or 4')
        return values


class PostDetail(PostBase):
    owner: UserSummary


class PostStatusUpdate(BaseModel):
    status: PostStatus


class ContactViewResponse(ORMModel):
    id: int
    post_id: int
    viewer_id: int
    created_at: datetime
    has_confirmed: bool
    is_deal: bool

    class Config:
        orm_mode = True


class DealConfirmationRequest(BaseModel):
    is_deal: bool


class InviteRecordResponse(ORMModel):
    id: int
    inviter_id: int
    invitee_id: int
    reward_granted: bool
    created_at: datetime

    class Config:
        orm_mode = True


class DashboardResponse(BaseModel):
    points: int
    deal_rate: float
    total_posts: int
    active_posts: int


class Pagination(BaseModel):
    total: int
    items: List[PostListItem]

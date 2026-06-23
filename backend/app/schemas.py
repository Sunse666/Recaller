import datetime
from typing import Optional, List
from pydantic import BaseModel


# ── Person ──

class PersonCreate(BaseModel):
    name: str
    remark: Optional[str] = None
    signature: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = 0
    notes: Optional[str] = None
    birthday: Optional[str] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    remark: Optional[str] = None
    signature: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    circle_tags: Optional[List[str]] = None
    impression_tags: Optional[List[str]] = None
    importance: Optional[int] = None
    notes: Optional[str] = None
    birthday: Optional[str] = None


class PersonBrief(BaseModel):
    id: int
    name: str
    remark: Optional[str] = None
    signature: Optional[str] = None
    avatar: Optional[str] = None
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = 0
    account_count: int = 0

    model_config = {"from_attributes": True}


class PersonDetail(BaseModel):
    id: int
    name: str
    remark: Optional[str] = None
    signature: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = 0
    notes: Optional[str] = None
    birthday: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


# ── Account ──

class AccountCreate(BaseModel):
    account_type: str
    account_identifier: str
    current_nickname: Optional[str] = None
    current_avatar: Optional[str] = None


class AccountUpdate(BaseModel):
    account_type: Optional[str] = None
    account_identifier: Optional[str] = None
    current_nickname: Optional[str] = None
    current_avatar: Optional[str] = None


class AccountBrief(BaseModel):
    id: int
    account_type: str
    account_identifier: str
    current_nickname: Optional[str] = None
    current_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class AccountDetail(BaseModel):
    id: int
    person_id: int
    account_type: str
    account_identifier: str
    current_nickname: Optional[str] = None
    current_avatar: Optional[str] = None
    nickname_histories: List["NicknameHistoryBrief"] = []

    model_config = {"from_attributes": True}


# ── Nickname History ──

class NicknameHistoryCreate(BaseModel):
    nickname: str
    avatar: Optional[str] = None
    changed_at: datetime.datetime


class NicknameHistoryBrief(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    changed_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Group ──

class GroupCreate(BaseModel):
    group_number: str
    group_name: str
    remark: Optional[str] = None
    tags: List[str] = []
    avatar: Optional[str] = None


class GroupUpdate(BaseModel):
    group_name: Optional[str] = None
    remark: Optional[str] = None
    tags: Optional[List[str]] = None
    avatar: Optional[str] = None


class GroupBrief(BaseModel):
    id: int
    group_number: str
    group_name: str
    remark: Optional[str] = None
    tags: List[str] = []
    avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class GroupDetail(BaseModel):
    id: int
    group_number: str
    group_name: str
    remark: Optional[str] = None
    tags: List[str] = []
    avatar: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


# ── Group Membership ──

class MembershipCreate(BaseModel):
    account_id: int
    group_id: int
    group_nickname: Optional[str] = None
    joined_at: Optional[datetime.datetime] = None
    left_at: Optional[datetime.datetime] = None
    is_pinned: bool = False
    is_muted: bool = False


class MembershipUpdate(BaseModel):
    group_nickname: Optional[str] = None
    joined_at: Optional[datetime.datetime] = None
    left_at: Optional[datetime.datetime] = None
    is_pinned: Optional[bool] = None
    is_muted: Optional[bool] = None


class MembershipBrief(BaseModel):
    id: int
    account_id: int
    group_id: int
    group_nickname: Optional[str] = None
    joined_at: Optional[datetime.datetime] = None
    left_at: Optional[datetime.datetime] = None
    is_pinned: bool = False
    is_muted: bool = False
    group: Optional[GroupBrief] = None

    model_config = {"from_attributes": True}

# ── Person Relation ──

class RelationCreate(BaseModel):
    person_id_2: int
    relation_type: Optional[str] = None


class RelationBrief(BaseModel):
    id: int
    person_id_1: int
    person_id_2: int
    relation_type: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Person Meeting ──

class MeetingCreate(BaseModel):
    description: str
    met_at: Optional[str] = None


class MeetingBrief(BaseModel):
    id: int
    description: str
    met_at: Optional[str] = None

    model_config = {"from_attributes": True}

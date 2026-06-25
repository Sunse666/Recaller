import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class LimitsConfig(BaseModel):
    upload_rate_per_min: int = 10
    upload_max_size_mb: int = 10
    upload_max_px: int = 2048

class UserBrief(BaseModel):
    uid: str
    username: str
    role: str
    model_config = {"from_attributes": True}

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = Field(default=None, max_length=10)
    description: Optional[str] = Field(default=None, max_length=200)
    card_label: str = Field(default="图片", max_length=50)
    cards_label: str = Field(default="图片", max_length=50)
    group_label: str = Field(default="图组", max_length=50)
    groups_label: str = Field(default="图组", max_length=50)
    board_type: str = Field(default="image", max_length=20)
    field_config: dict = {}
    is_public: bool = False
    sort_order: int = 0

class BoardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    icon: Optional[str] = Field(default=None, max_length=10)
    description: Optional[str] = Field(default=None, max_length=200)
    card_label: Optional[str] = Field(default=None, max_length=50)
    cards_label: Optional[str] = Field(default=None, max_length=50)
    group_label: Optional[str] = Field(default=None, max_length=50)
    groups_label: Optional[str] = Field(default=None, max_length=50)
    board_type: Optional[str] = Field(default=None, max_length=20)
    field_config: Optional[dict] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None

class BoardResponse(BaseModel):
    id: int
    user_id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    card_label: str
    cards_label: str
    group_label: str
    groups_label: str
    board_type: str
    field_config: dict
    is_public: bool
    sort_order: int
    created_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}

class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    remark: Optional[str] = Field(default=None, max_length=100)
    signature: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = Field(default=None, max_length=100)
    avatar: Optional[str] = Field(default=None, max_length=500)
    card_bg: Optional[str] = Field(default=None, max_length=500)
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = Field(default=0, ge=0, le=5, description="重要性 0-5")
    notes: Optional[str] = Field(default=None, max_length=2000)
    birthday: Optional[str] = Field(default=None, max_length=20)
    board_id: Optional[int] = None

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    remark: Optional[str] = Field(default=None, max_length=100)
    signature: Optional[str] = Field(default=None, max_length=200)
    location: Optional[str] = Field(default=None, max_length=100)
    avatar: Optional[str] = Field(default=None, max_length=500)
    card_bg: Optional[str] = Field(default=None, max_length=500)
    circle_tags: Optional[List[str]] = None
    impression_tags: Optional[List[str]] = None
    importance: Optional[int] = Field(default=None, ge=0, le=5)
    notes: Optional[str] = Field(default=None, max_length=2000)
    birthday: Optional[str] = Field(default=None, max_length=20)
    board_id: Optional[int] = None

class PersonBrief(BaseModel):
    id: int
    name: str
    remark: Optional[str] = None
    signature: Optional[str] = None
    avatar: Optional[str] = None
    card_bg: Optional[str] = None
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = 0
    account_count: int = 0
    board_id: Optional[int] = None
    model_config = {"from_attributes": True}

class PersonDetail(BaseModel):
    id: int
    name: str
    remark: Optional[str] = None
    signature: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None
    card_bg: Optional[str] = None
    circle_tags: List[str] = []
    impression_tags: List[str] = []
    importance: int = 0
    notes: Optional[str] = None
    birthday: Optional[str] = None
    board_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}

class AccountCreate(BaseModel):
    account_type: str = Field(..., min_length=1, max_length=20)
    account_identifier: str = Field(..., min_length=1, max_length=100)
    current_nickname: Optional[str] = Field(default=None, max_length=50)
    current_avatar: Optional[str] = Field(default=None, max_length=500)

class AccountUpdate(BaseModel):
    account_type: Optional[str] = Field(default=None, min_length=1, max_length=20)
    account_identifier: Optional[str] = Field(default=None, min_length=1, max_length=100)
    current_nickname: Optional[str] = Field(default=None, max_length=50)
    current_avatar: Optional[str] = Field(default=None, max_length=500)

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

class NicknameHistoryCreate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)
    avatar: Optional[str] = Field(default=None, max_length=500)
    changed_at: datetime.datetime

class NicknameHistoryBrief(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    changed_at: datetime.datetime

    model_config = {"from_attributes": True}

class GroupCreate(BaseModel):
    group_number: str = Field(..., min_length=1, max_length=50)
    group_name: str = Field(..., min_length=1, max_length=50)
    remark: Optional[str] = Field(default=None, max_length=100)
    tags: List[str] = []
    avatar: Optional[str] = Field(default=None, max_length=500)
    board_id: Optional[int] = None

class GroupUpdate(BaseModel):
    group_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    remark: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = None
    avatar: Optional[str] = Field(default=None, max_length=500)
    board_id: Optional[int] = None

class GroupBrief(BaseModel):
    id: int
    group_number: str
    group_name: str
    remark: Optional[str] = None
    tags: List[str] = []
    avatar: Optional[str] = None
    board_id: Optional[int] = None
    model_config = {"from_attributes": True}

class GroupDetail(BaseModel):
    id: int
    group_number: str
    group_name: str
    remark: Optional[str] = None
    tags: List[str] = []
    avatar: Optional[str] = None
    board_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    model_config = {"from_attributes": True}

class MembershipCreate(BaseModel):
    account_id: int
    group_nickname: Optional[str] = Field(default=None, max_length=50)
    joined_at: Optional[datetime.datetime] = None
    left_at: Optional[datetime.datetime] = None
    is_pinned: bool = False
    is_muted: bool = False

class MembershipUpdate(BaseModel):
    group_nickname: Optional[str] = Field(default=None, max_length=50)
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

class RelationCreate(BaseModel):
    person_id_2: int
    relation_type: Optional[str] = Field(default=None, max_length=50)

class RelationBrief(BaseModel):
    id: int
    person_id_1: int
    person_id_2: int
    relation_type: Optional[str] = None

    model_config = {"from_attributes": True}

class MeetingCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    met_at: Optional[str] = Field(default=None, max_length=100)

class MeetingBrief(BaseModel):
    id: int
    description: str
    met_at: Optional[str] = None

    model_config = {"from_attributes": True}

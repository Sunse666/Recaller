import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base

def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(21), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(10), nullable=False, default="user")
    enabled = Column(Boolean, default=True, nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    avatar = Column(String(500), nullable=True)
    limits = Column(Text, default="{}")
    created_at = Column(DateTime, default=_utcnow)

    boards = relationship("Board", back_populates="user", cascade="all, delete-orphan")

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), nullable=True)
    description = Column(String(200), nullable=True)
    card_label = Column(String(50), nullable=False, default="图片")
    cards_label = Column(String(50), nullable=False, default="图片")
    group_label = Column(String(50), nullable=False, default="图组")
    groups_label = Column(String(50), nullable=False, default="图组")
    board_type = Column(String(20), nullable=False, default="image")
    field_config = Column(Text, default="{}")
    is_public = Column(Boolean, default=False)
    random_order = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="boards")
    persons = relationship("Person", back_populates="board", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="board", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="board", cascade="all, delete-orphan")

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    remark = Column(String(200), nullable=True)
    signature = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    avatar = Column(String(2000), nullable=True)
    card_bg = Column(String(2000), nullable=True)
    circle_tags = Column(Text, default="[]")
    impression_tags = Column(Text, default="[]")
    importance = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    birthday = Column(String(20), nullable=True)
    allow_download = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    board = relationship("Board", back_populates="persons")
    accounts = relationship("Account", back_populates="person", cascade="all, delete-orphan")
    relations_from = relationship("PersonRelation", foreign_keys="PersonRelation.person_id_1", cascade="all, delete-orphan")
    relations_to = relationship("PersonRelation", foreign_keys="PersonRelation.person_id_2", cascade="all, delete-orphan")
    meetings = relationship("PersonMeeting", back_populates="person", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=True, index=True)
    account_type = Column(String(50), nullable=False)
    account_identifier = Column(String(200), nullable=False)
    current_nickname = Column(String(200), nullable=True)
    current_avatar = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    board = relationship("Board", back_populates="accounts")
    person = relationship("Person", back_populates="accounts")
    nickname_histories = relationship("AccountNicknameHistory", back_populates="account", cascade="all, delete-orphan")
    memberships = relationship("GroupMembership", back_populates="account", cascade="all, delete-orphan")

class AccountNicknameHistory(Base):
    __tablename__ = "account_nickname_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    nickname = Column(String(200), nullable=False)
    avatar = Column(String(2000), nullable=True)
    changed_at = Column(DateTime, nullable=False)

    account = relationship("Account", back_populates="nickname_histories")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=True, index=True)
    group_number = Column(String(100), nullable=False, unique=True, index=True)
    group_name = Column(String(200), nullable=False)
    remark = Column(String(200), nullable=True)
    tags = Column(Text, default="[]")
    avatar = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    board = relationship("Board", back_populates="groups")
    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    group_nickname = Column(String(200), nullable=True)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    is_pinned = Column(Boolean, default=False)
    is_muted = Column(Boolean, default=False)

    account = relationship("Account", back_populates="memberships")
    group = relationship("Group", back_populates="memberships")

class PersonRelation(Base):
    __tablename__ = "person_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id_1 = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id_2 = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(100), nullable=True)

    person_1 = relationship("Person", foreign_keys=[person_id_1], back_populates="relations_from")
    person_2 = relationship("Person", foreign_keys=[person_id_2], back_populates="relations_to")

class PersonMeeting(Base):
    __tablename__ = "person_meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    met_at = Column(String(200), nullable=True)

    person = relationship("Person", back_populates="meetings")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    action = Column(String(20), nullable=False)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    uid = Column(String(21), nullable=False)
    role = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)

class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    purpose = Column(String(20), nullable=False, default="register")
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)

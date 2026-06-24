import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Group, GroupMembership, Account, Board, User
from ..auth import require_admin, require_user
from ..audit import log as audit_log
from .. import schemas

router = APIRouter(prefix="/api/groups", tags=["groups"])


def _group_to_detail(g: Group) -> schemas.GroupDetail:
    return schemas.GroupDetail(
        id=g.id, group_number=g.group_number, group_name=g.group_name,
        remark=g.remark, tags=json.loads(g.tags or "[]"), avatar=g.avatar,
        board_id=g.board_id, created_at=g.created_at,
    )


def _get_default_board(user: dict, db: Session) -> int | None:
    u = db.query(User).filter(User.uid == user["uid"]).first()
    if not u:
        return None
    b = db.query(Board).filter(Board.user_id == u.id).order_by(Board.sort_order).first()
    return b.id if b else None


@router.get("", response_model=list[schemas.GroupDetail])
def list_groups(search: str = "", board_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Group)
    if board_id:
        query = query.filter(Group.board_id == board_id)
    if search:
        like = f"%{search}%"
        query = query.filter((Group.group_name.ilike(like)) | (Group.group_number.ilike(like)))
    return [_group_to_detail(g) for g in query.all()]


@router.get("/{group_id}", response_model=schemas.GroupDetail)
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    return _group_to_detail(g)


@router.post("", response_model=schemas.GroupDetail, status_code=201)
def create_group(data: schemas.GroupCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    bid = data.board_id or _get_default_board(user, db)
    if not bid:
        raise HTTPException(status_code=400, detail="请先创建一个画板")
    existing = db.query(Group).filter(Group.group_number == data.group_number, Group.board_id == bid).first()
    if existing:
        raise HTTPException(status_code=400, detail="该群号在当前画板中已存在")
    g = Group(
        board_id=bid, group_number=data.group_number, group_name=data.group_name,
        remark=data.remark, tags=json.dumps(data.tags, ensure_ascii=False), avatar=data.avatar,
    )
    db.add(g); db.flush()
    audit_log(db, user["username"], "create", "group", g.id, {"name": data.group_name, "board_id": bid})
    db.commit(); db.refresh(g)
    return _group_to_detail(g)


@router.put("/{group_id}", response_model=schemas.GroupDetail)
def update_group(group_id: int, data: schemas.GroupUpdate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    changed = {}
    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "tags" and val is not None:
            setattr(g, field, json.dumps(val, ensure_ascii=False)); changed[field] = True
        elif val is not None:
            setattr(g, field, val); changed[field] = True
    if changed:
        audit_log(db, user["username"], "update", "group", group_id, {"changed_fields": list(changed.keys())})
    db.commit(); db.refresh(g)
    return _group_to_detail(g)


@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    info = {"name": g.group_name, "number": g.group_number}
    db.delete(g)
    audit_log(db, user["username"], "delete", "group", group_id, info)
    db.commit()


@router.get("/{group_id}/members", response_model=list[schemas.AccountBrief])
def list_group_members(group_id: int, db: Session = Depends(get_db)):
    memberships = (
        db.query(GroupMembership).options(joinedload(GroupMembership.account))
        .filter(GroupMembership.group_id == group_id).all()
    )
    return [
        schemas.AccountBrief(
            id=m.account.id, account_type=m.account.account_type,
            account_identifier=m.account.account_identifier,
            current_nickname=m.account.current_nickname, current_avatar=m.account.current_avatar,
        )
        for m in memberships if m.account
    ]


@router.post("/{group_id}/members", response_model=schemas.MembershipBrief, status_code=201)
def add_member(group_id: int, data: schemas.MembershipCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    a = db.query(Account).get(data.account_id)
    if not a:
        raise HTTPException(status_code=404, detail="账号不存在")
    existing = db.query(GroupMembership).filter(
        GroupMembership.account_id == data.account_id, GroupMembership.group_id == group_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该账号已在此群中")
    m = GroupMembership(
        account_id=data.account_id, group_id=group_id, group_nickname=data.group_nickname,
        joined_at=data.joined_at, left_at=data.left_at,
        is_pinned=data.is_pinned, is_muted=data.is_muted,
    )
    db.add(m); db.flush()
    audit_log(db, user["username"], "create", "membership", m.id, {"group_id": group_id, "account_id": data.account_id})
    db.commit(); db.refresh(m)
    return schemas.MembershipBrief(
        id=m.id, account_id=m.account_id, group_id=m.group_id,
        group_nickname=m.group_nickname, joined_at=m.joined_at,
        left_at=m.left_at, is_pinned=m.is_pinned, is_muted=m.is_muted,
    )


@router.put("/{group_id}/members/{membership_id}", response_model=schemas.MembershipBrief)
def update_membership(group_id: int, membership_id: int, data: schemas.MembershipUpdate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    m = db.query(GroupMembership).filter(
        GroupMembership.id == membership_id, GroupMembership.group_id == group_id,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="成员关系不存在")
    changed = {}
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(m, field, val); changed[field] = True
    if changed:
        audit_log(db, user["username"], "update", "membership", membership_id, {"changed_fields": list(changed.keys())})
    db.commit(); db.refresh(m)
    return schemas.MembershipBrief(
        id=m.id, account_id=m.account_id, group_id=m.group_id,
        group_nickname=m.group_nickname, joined_at=m.joined_at,
        left_at=m.left_at, is_pinned=m.is_pinned, is_muted=m.is_muted,
    )


@router.delete("/{group_id}/members/{membership_id}", status_code=204)
def remove_member(group_id: int, membership_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    m = db.query(GroupMembership).filter(
        GroupMembership.id == membership_id, GroupMembership.group_id == group_id,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="成员关系不存在")
    db.delete(m)
    audit_log(db, user["username"], "delete", "membership", membership_id, {"group_id": group_id})
    db.commit()

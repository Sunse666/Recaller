import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Group, GroupMembership, Account
from .. import schemas

router = APIRouter(prefix="/api/groups", tags=["groups"])


def _group_to_detail(g: Group) -> schemas.GroupDetail:
    return schemas.GroupDetail(
        id=g.id,
        group_number=g.group_number,
        group_name=g.group_name,
        remark=g.remark,
        tags=json.loads(g.tags or "[]"),
        avatar=g.avatar,
        created_at=g.created_at,
    )


@router.get("", response_model=list[schemas.GroupDetail])
def list_groups(search: str = "", db: Session = Depends(get_db)):
    query = db.query(Group)
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
def create_group(data: schemas.GroupCreate, db: Session = Depends(get_db)):
    existing = db.query(Group).filter(Group.group_number == data.group_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="该群号已存在")
    g = Group(
        group_number=data.group_number,
        group_name=data.group_name,
        remark=data.remark,
        tags=json.dumps(data.tags, ensure_ascii=False),
        avatar=data.avatar,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _group_to_detail(g)


@router.put("/{group_id}", response_model=schemas.GroupDetail)
def update_group(group_id: int, data: schemas.GroupUpdate, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "tags" and val is not None:
            setattr(g, field, json.dumps(val, ensure_ascii=False))
        elif val is not None:
            setattr(g, field, val)
    db.commit()
    db.refresh(g)
    return _group_to_detail(g)


@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    db.delete(g)
    db.commit()


# ── Group Members ──

@router.get("/{group_id}/members", response_model=list[schemas.AccountBrief])
def list_group_members(group_id: int, db: Session = Depends(get_db)):
    memberships = (
        db.query(GroupMembership)
        .options(joinedload(GroupMembership.account))
        .filter(GroupMembership.group_id == group_id)
        .all()
    )
    return [
        schemas.AccountBrief(
            id=m.account.id,
            account_type=m.account.account_type,
            account_identifier=m.account.account_identifier,
            current_nickname=m.account.current_nickname,
            current_avatar=m.account.current_avatar,
        )
        for m in memberships
        if m.account
    ]


# ── Add/remove account to/from group ──

@router.post("/{group_id}/members", response_model=schemas.MembershipBrief, status_code=201)
def add_member(group_id: int, data: schemas.MembershipCreate, db: Session = Depends(get_db)):
    g = db.query(Group).get(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="群不存在")
    a = db.query(Account).get(data.account_id)
    if not a:
        raise HTTPException(status_code=404, detail="账号不存在")
    existing = db.query(GroupMembership).filter(
        GroupMembership.account_id == data.account_id,
        GroupMembership.group_id == group_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该账号已在此群中")
    m = GroupMembership(
        account_id=data.account_id,
        group_id=group_id,
        group_nickname=data.group_nickname,
        joined_at=data.joined_at,
        left_at=data.left_at,
        is_pinned=data.is_pinned,
        is_muted=data.is_muted,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return schemas.MembershipBrief(
        id=m.id, account_id=m.account_id, group_id=m.group_id,
        group_nickname=m.group_nickname, joined_at=m.joined_at,
        left_at=m.left_at, is_pinned=m.is_pinned, is_muted=m.is_muted,
    )


@router.put("/{group_id}/members/{membership_id}", response_model=schemas.MembershipBrief)
def update_membership(group_id: int, membership_id: int, data: schemas.MembershipUpdate, db: Session = Depends(get_db)):
    m = db.query(GroupMembership).filter(
        GroupMembership.id == membership_id,
        GroupMembership.group_id == group_id,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="成员关系不存在")
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(m, field, val)
    db.commit()
    db.refresh(m)
    return schemas.MembershipBrief(
        id=m.id, account_id=m.account_id, group_id=m.group_id,
        group_nickname=m.group_nickname, joined_at=m.joined_at,
        left_at=m.left_at, is_pinned=m.is_pinned, is_muted=m.is_muted,
    )


@router.delete("/{group_id}/members/{membership_id}", status_code=204)
def remove_member(group_id: int, membership_id: int, db: Session = Depends(get_db)):
    m = db.query(GroupMembership).filter(
        GroupMembership.id == membership_id,
        GroupMembership.group_id == group_id,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="成员关系不存在")
    db.delete(m)
    db.commit()

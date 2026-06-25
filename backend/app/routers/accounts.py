import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Person, Account, AccountNicknameHistory, GroupMembership
from ..auth import require_admin, require_user, optional_user, require_board_owner, require_person_owner, check_board_visible
from ..audit import log as audit_log
from .. import schemas

router = APIRouter(prefix="/api/persons/{person_id}/accounts", tags=["accounts"])


def _account_to_detail(a: Account) -> schemas.AccountDetail:
    return schemas.AccountDetail(
        id=a.id, person_id=a.person_id,
        account_type=a.account_type, account_identifier=a.account_identifier,
        current_nickname=a.current_nickname, current_avatar=a.current_avatar,
        nickname_histories=[
            schemas.NicknameHistoryBrief(id=h.id, nickname=h.nickname, avatar=h.avatar, changed_at=h.changed_at)
            for h in (a.nickname_histories or [])
        ],
    )


@router.get("", response_model=list[schemas.AccountDetail])
def list_accounts(person_id: int, db: Session = Depends(get_db), user: dict | None = Depends(optional_user)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="条目不存在")
    if p.board_id:
        check_board_visible(db, p.board_id, user)
    accounts = (
        db.query(Account).options(joinedload(Account.nickname_histories))
        .filter(Account.person_id == person_id).all()
    )
    return [_account_to_detail(a) for a in accounts]


@router.post("", response_model=schemas.AccountDetail, status_code=201)
def create_account(person_id: int, data: schemas.AccountCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    p = require_person_owner(db, person_id, user)
    a = Account(
        person_id=person_id, board_id=p.board_id,
        account_type=data.account_type, account_identifier=data.account_identifier,
        current_nickname=data.current_nickname, current_avatar=data.current_avatar,
    )
    db.add(a); db.flush()
    audit_log(db, user["username"], "create", "account", a.id, {"person_id": person_id, "type": data.account_type, "identifier": data.account_identifier})
    db.commit(); db.refresh(a)
    return _account_to_detail(a)


@router.put("/{account_id}", response_model=schemas.AccountDetail)
def update_account(person_id: int, account_id: int, data: schemas.AccountUpdate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    a = db.query(Account).options(joinedload(Account.nickname_histories)).filter(
        Account.id == account_id, Account.person_id == person_id
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="关联账号不存在")
    changed = False
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(a, field, val); changed = True
    if changed:
        audit_log(db, user["username"], "update", "account", account_id, {"changed_fields": list(data.model_dump(exclude_unset=True).keys())})
    db.commit(); db.refresh(a)
    return _account_to_detail(a)


@router.delete("/{account_id}", status_code=204)
def delete_account(person_id: int, account_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    a = db.query(Account).filter(Account.id == account_id, Account.person_id == person_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="关联账号不存在")
    info = {"person_id": person_id, "type": a.account_type, "identifier": a.account_identifier}
    db.delete(a)
    audit_log(db, user["username"], "delete", "account", account_id, info)
    db.commit()


@router.post("/{account_id}/nicknames", response_model=schemas.NicknameHistoryBrief, status_code=201)
def add_nickname_history(
    person_id: int, account_id: int, data: schemas.NicknameHistoryCreate,
    db: Session = Depends(get_db), user: dict = Depends(require_user),
):
    require_person_owner(db, person_id, user)
    a = db.query(Account).filter(Account.id == account_id, Account.person_id == person_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="关联账号不存在")
    h = AccountNicknameHistory(account_id=account_id, nickname=data.nickname, avatar=data.avatar, changed_at=data.changed_at)
    db.add(h); db.flush()
    audit_log(db, user["username"], "create", "nickname_history", h.id, {"account_id": account_id, "nickname": data.nickname})
    db.commit(); db.refresh(h)
    return h


@router.delete("/{account_id}/nicknames/{history_id}", status_code=204)
def remove_nickname_history(
    person_id: int, account_id: int, history_id: int,
    db: Session = Depends(get_db), user: dict = Depends(require_user),
):
    require_person_owner(db, person_id, user)
    h = db.query(AccountNicknameHistory).join(Account).filter(
        AccountNicknameHistory.id == history_id,
        AccountNicknameHistory.account_id == account_id,
        Account.person_id == person_id,
    ).first()
    if not h:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    db.delete(h)
    audit_log(db, user["username"], "delete", "nickname_history", history_id, {"account_id": account_id})
    db.commit()


@router.get("/{account_id}/memberships", response_model=list[schemas.MembershipBrief])
def list_memberships(person_id: int, account_id: int, db: Session = Depends(get_db), user: dict | None = Depends(optional_user)):
    p = db.query(Person).get(person_id)
    if p and p.board_id:
        check_board_visible(db, p.board_id, user)
    a = db.query(Account).filter(Account.id == account_id, Account.person_id == person_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="关联账号不存在")
    memberships = (
        db.query(GroupMembership).options(joinedload(GroupMembership.group))
        .filter(GroupMembership.account_id == account_id)
        .order_by(GroupMembership.is_pinned.desc(), GroupMembership.id).all()
    )
    return [
        schemas.MembershipBrief(
            id=m.id, account_id=m.account_id, group_id=m.group_id,
            group_nickname=m.group_nickname, joined_at=m.joined_at,
            left_at=m.left_at, is_pinned=m.is_pinned, is_muted=m.is_muted,
            group=schemas.GroupBrief(
                id=m.group.id, group_number=m.group.group_number, group_name=m.group.group_name,
                remark=m.group.remark, tags=json.loads(m.group.tags or "[]"), avatar=m.group.avatar,
            ) if m.group else None,
        )
        for m in memberships
    ]

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Person, Account, PersonRelation, PersonMeeting, Board
from ..auth import require_admin, require_user, optional_user, get_user_by_uid, require_board_owner, get_default_board_id, require_person_owner, check_board_visible
from ..encryption import encrypt, decrypt
from ..audit import log as audit_log
from .. import schemas

router = APIRouter(prefix="/api/persons", tags=["persons"])

def _person_to_brief(p: Person) -> schemas.PersonBrief:
    return schemas.PersonBrief(
        id=p.id, name=p.name, remark=p.remark, signature=p.signature,
        avatar=p.avatar, card_bg=p.card_bg,
        circle_tags=json.loads(p.circle_tags or "[]"),
        impression_tags=json.loads(p.impression_tags or "[]"),
        importance=p.importance,
        account_count=len(p.accounts) if p.accounts else 0,
        board_id=p.board_id,
    )

def _person_to_detail(p: Person) -> schemas.PersonDetail:
    return schemas.PersonDetail(
        id=p.id, name=p.name, remark=p.remark, signature=p.signature,
        location=p.location, avatar=p.avatar, card_bg=p.card_bg,
        circle_tags=json.loads(p.circle_tags or "[]"),
        impression_tags=json.loads(p.impression_tags or "[]"),
        importance=p.importance, notes=decrypt(p.notes), birthday=p.birthday,
        board_id=p.board_id,
        created_at=p.created_at, updated_at=p.updated_at,
    )

@router.get("", response_model=list[schemas.PersonBrief])
def list_persons(
    search: str = Query(default=""),
    board_id: int = Query(default=None),
    db: Session = Depends(get_db),
    user: dict | None = Depends(optional_user),
):
    query = db.query(Person).options(joinedload(Person.accounts))
    if board_id:
        query = query.filter(Person.board_id == board_id)
    if search:
        like = f"%{search}%"
        query = query.outerjoin(Person.accounts).filter(
            (Person.name.ilike(like))
            | (Person.remark.ilike(like))
            | (Person.circle_tags.ilike(like))
            | (Person.impression_tags.ilike(like))
            | (Person.signature.ilike(like))
            | (Person.notes.ilike(like))
            | (Account.account_identifier.ilike(like))
            | (Account.current_nickname.ilike(like))
        ).distinct()

    if board_id:
        pass
    elif user is None:
        public_ids = [b.id for b in db.query(Board).filter(Board.is_public == True).all()]
        query = query.filter(Person.board_id.in_(public_ids))
    elif user["role"] != "admin":
        u = get_user_by_uid(db, user["uid"])
        if u:
            own_ids = [b.id for b in db.query(Board).filter(Board.user_id == u.id).all()]
            if own_ids:
                query = query.filter(Person.board_id.in_(own_ids))
            else:
                return []

    persons = query.order_by(Person.importance.desc(), Person.name).all()
    return [_person_to_brief(p) for p in persons]

@router.get("/{person_id}", response_model=schemas.PersonDetail)
def get_person(person_id: int, db: Session = Depends(get_db), user: dict | None = Depends(optional_user)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="条目不存在")
    if p.board_id:
        board = db.query(Board).filter(Board.id == p.board_id).first()
        if board and not board.is_public:
            if user is None:
                raise HTTPException(status_code=403, detail="无权访问")
            require_board_owner(db, p.board_id, user)
    return _person_to_detail(p)

@router.post("", response_model=schemas.PersonDetail, status_code=201)
def create_person(data: schemas.PersonCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    bid = data.board_id or get_default_board_id(db, user)
    if not bid:
        raise HTTPException(status_code=400, detail="请先创建一个画板")
    require_board_owner(db, bid, user)
    p = Person(
        board_id=bid, name=data.name, remark=data.remark,
        signature=data.signature, location=data.location, avatar=data.avatar,
        card_bg=data.card_bg,
        circle_tags=json.dumps(data.circle_tags, ensure_ascii=False),
        impression_tags=json.dumps(data.impression_tags, ensure_ascii=False),
        importance=data.importance, notes=encrypt(data.notes), birthday=data.birthday,
    )
    db.add(p); db.flush()
    audit_log(db, user["username"], "create", "person", p.id, {"name": data.name, "board_id": bid})
    db.commit(); db.refresh(p)
    return _person_to_detail(p)

@router.put("/{person_id}", response_model=schemas.PersonDetail)
def update_person(person_id: int, data: schemas.PersonUpdate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    p = require_person_owner(db, person_id, user)
    changed = False
    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "board_id" and val is not None and val != p.board_id:
            require_board_owner(db, val, user)
        if field == "notes" and val is not None:
            setattr(p, field, encrypt(val)); changed = True
        elif field in ("circle_tags", "impression_tags") and val is not None:
            setattr(p, field, json.dumps(val, ensure_ascii=False)); changed = True
        elif val is not None:
            setattr(p, field, val); changed = True
    if changed:
        audit_log(db, user["username"], "update", "person", person_id, {"changed_fields": list(data.model_dump(exclude_unset=True).keys())})
    db.commit(); db.refresh(p)
    return _person_to_detail(p)

@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    p = require_person_owner(db, person_id, user)
    name = p.name
    db.delete(p)
    audit_log(db, user["username"], "delete", "person", person_id, {"name": name})
    db.commit()

@router.get("/{person_id}/relations", response_model=list[schemas.RelationBrief])
def list_relations(person_id: int, db: Session = Depends(get_db), user: dict | None = Depends(optional_user)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="条目不存在")
    if p.board_id:
        check_board_visible(db, p.board_id, user)
    o = db.query(PersonRelation).filter(PersonRelation.person_id_1 == person_id).all()
    i = db.query(PersonRelation).filter(PersonRelation.person_id_2 == person_id).all()
    return o + i

@router.post("/{person_id}/relations", response_model=schemas.RelationBrief, status_code=201)
def add_relation(person_id: int, data: schemas.RelationCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    if data.person_id_2 == person_id:
        raise HTTPException(status_code=400, detail="不能和自己建立关系")
    exists = db.query(PersonRelation).filter(
        (PersonRelation.person_id_1 == person_id) & (PersonRelation.person_id_2 == data.person_id_2)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="关系已存在")
    rel = PersonRelation(person_id_1=person_id, person_id_2=data.person_id_2, relation_type=data.relation_type)
    db.add(rel); db.flush()
    audit_log(db, user["username"], "create", "relation", rel.id, {"p1": person_id, "p2": data.person_id_2})
    db.commit(); db.refresh(rel)
    return rel

@router.delete("/{person_id}/relations/{relation_id}", status_code=204)
def remove_relation(person_id: int, relation_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    rel = db.query(PersonRelation).filter(
        PersonRelation.id == relation_id,
        (PersonRelation.person_id_1 == person_id) | (PersonRelation.person_id_2 == person_id),
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="关系不存在")
    db.delete(rel)
    audit_log(db, user["username"], "delete", "relation", relation_id, {"p1": rel.person_id_1, "p2": rel.person_id_2})
    db.commit()

@router.get("/{person_id}/meetings", response_model=list[schemas.MeetingBrief])
def list_meetings(person_id: int, db: Session = Depends(get_db), user: dict | None = Depends(optional_user)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="条目不存在")
    if p.board_id:
        check_board_visible(db, p.board_id, user)
    return db.query(PersonMeeting).filter(PersonMeeting.person_id == person_id).all()

@router.post("/{person_id}/meetings", response_model=schemas.MeetingBrief, status_code=201)
def add_meeting(person_id: int, data: schemas.MeetingCreate, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    m = PersonMeeting(person_id=person_id, description=data.description, met_at=data.met_at)
    db.add(m); db.flush()
    audit_log(db, user["username"], "create", "meeting", m.id, {"person_id": person_id})
    db.commit(); db.refresh(m)
    return m

@router.delete("/{person_id}/meetings/{meeting_id}", status_code=204)
def remove_meeting(person_id: int, meeting_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    require_person_owner(db, person_id, user)
    m = db.query(PersonMeeting).filter(PersonMeeting.id == meeting_id, PersonMeeting.person_id == person_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="相遇记录不存在")
    db.delete(m)
    audit_log(db, user["username"], "delete", "meeting", meeting_id, {"person_id": person_id})
    db.commit()

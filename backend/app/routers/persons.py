import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Person, Account, PersonRelation, PersonMeeting, GroupMembership
from .. import schemas

router = APIRouter(prefix="/api/persons", tags=["persons"])

def _person_to_brief(p: Person) -> schemas.PersonBrief:
    return schemas.PersonBrief(
        id=p.id,
        name=p.name,
        remark=p.remark,
        signature=p.signature,
        avatar=p.avatar,
        circle_tags=json.loads(p.circle_tags or "[]"),
        impression_tags=json.loads(p.impression_tags or "[]"),
        importance=p.importance,
        account_count=len(p.accounts) if p.accounts else 0,
    )

def _person_to_detail(p: Person) -> schemas.PersonDetail:
    return schemas.PersonDetail(
        id=p.id,
        name=p.name,
        remark=p.remark,
        signature=p.signature,
        location=p.location,
        avatar=p.avatar,
        circle_tags=json.loads(p.circle_tags or "[]"),
        impression_tags=json.loads(p.impression_tags or "[]"),
        importance=p.importance,
        notes=p.notes,
        birthday=p.birthday,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )

@router.get("", response_model=list[schemas.PersonBrief])
def list_persons(
    search: str = Query(default="", description="搜索昵称、备注、账号"),
    db: Session = Depends(get_db),
):
    query = db.query(Person).options(joinedload(Person.accounts))
    if search:
        like = f"%{search}%"
        query = query.outerjoin(Person.accounts).filter(
            (Person.name.ilike(like))
            | (Person.remark.ilike(like))
            | (Account.account_identifier.ilike(like))
            | (Account.current_nickname.ilike(like))
        ).distinct()
    persons = query.order_by(Person.importance.desc(), Person.name).all()
    return [_person_to_brief(p) for p in persons]

@router.get("/{person_id}", response_model=schemas.PersonDetail)
def get_person(person_id: int, db: Session = Depends(get_db)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="群友不存在")
    return _person_to_detail(p)

@router.post("", response_model=schemas.PersonDetail, status_code=201)
def create_person(data: schemas.PersonCreate, db: Session = Depends(get_db)):
    p = Person(
        name=data.name,
        remark=data.remark,
        signature=data.signature,
        location=data.location,
        avatar=data.avatar,
        circle_tags=json.dumps(data.circle_tags, ensure_ascii=False),
        impression_tags=json.dumps(data.impression_tags, ensure_ascii=False),
        importance=data.importance,
        notes=data.notes,
        birthday=data.birthday,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _person_to_detail(p)

@router.put("/{person_id}", response_model=schemas.PersonDetail)
def update_person(person_id: int, data: schemas.PersonUpdate, db: Session = Depends(get_db)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="群友不存在")
    for field, val in data.model_dump(exclude_unset=True).items():
        if field in ("circle_tags", "impression_tags") and val is not None:
            setattr(p, field, json.dumps(val, ensure_ascii=False))
        elif val is not None:
            setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return _person_to_detail(p)

@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: int, db: Session = Depends(get_db)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="群友不存在")
    db.delete(p)
    db.commit()

@router.get("/{person_id}/relations", response_model=list[schemas.RelationBrief])
def list_relations(person_id: int, db: Session = Depends(get_db)):
    p = db.query(Person).get(person_id)
    if not p:
        raise HTTPException(status_code=404, detail="群友不存在")
    outgoing = db.query(PersonRelation).filter(PersonRelation.person_id_1 == person_id).all()
    incoming = db.query(PersonRelation).filter(PersonRelation.person_id_2 == person_id).all()
    return outgoing + incoming

@router.post("/{person_id}/relations", response_model=schemas.RelationBrief, status_code=201)
def add_relation(person_id: int, data: schemas.RelationCreate, db: Session = Depends(get_db)):
    if data.person_id_2 == person_id:
        raise HTTPException(status_code=400, detail="不能和自己建立关系")
    exists = db.query(PersonRelation).filter(
        (PersonRelation.person_id_1 == person_id) & (PersonRelation.person_id_2 == data.person_id_2)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="关系已存在")
    rel = PersonRelation(person_id_1=person_id, person_id_2=data.person_id_2, relation_type=data.relation_type)
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel

@router.delete("/{person_id}/relations/{relation_id}", status_code=204)
def remove_relation(person_id: int, relation_id: int, db: Session = Depends(get_db)):
    rel = db.query(PersonRelation).filter(
        PersonRelation.id == relation_id,
        (PersonRelation.person_id_1 == person_id) | (PersonRelation.person_id_2 == person_id),
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="关系不存在")
    db.delete(rel)
    db.commit()

@router.get("/{person_id}/meetings", response_model=list[schemas.MeetingBrief])
def list_meetings(person_id: int, db: Session = Depends(get_db)):
    return db.query(PersonMeeting).filter(PersonMeeting.person_id == person_id).all()

@router.post("/{person_id}/meetings", response_model=schemas.MeetingBrief, status_code=201)
def add_meeting(person_id: int, data: schemas.MeetingCreate, db: Session = Depends(get_db)):
    m = PersonMeeting(person_id=person_id, description=data.description, met_at=data.met_at)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.delete("/{person_id}/meetings/{meeting_id}", status_code=204)
def remove_meeting(person_id: int, meeting_id: int, db: Session = Depends(get_db)):
    m = db.query(PersonMeeting).filter(
        PersonMeeting.id == meeting_id, PersonMeeting.person_id == person_id
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="相遇记录不存在")
    db.delete(m)
    db.commit()
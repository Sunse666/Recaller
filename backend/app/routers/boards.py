import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Board, User
from ..auth import require_admin, require_user, get_user_by_uid, require_board_owner
from ..audit import log as audit_log
from .. import schemas

router = APIRouter(prefix="/api/boards", tags=["boards"])

def _board_to_response(b: Board) -> schemas.BoardResponse:
    return schemas.BoardResponse(
        id=b.id,
        user_id=b.user_id,
        name=b.name,
        icon=b.icon,
        description=b.description,
        card_label=b.card_label,
        cards_label=b.cards_label,
        group_label=b.group_label,
        groups_label=b.groups_label,
        board_type=b.board_type,
        field_config=json.loads(b.field_config or "{}"),
        is_public=b.is_public,
        random_order=bool(b.random_order),
        sort_order=b.sort_order,
        created_at=b.created_at,
    )

@router.get("", response_model=list[schemas.BoardResponse])
def list_boards(
    uid: str = Query(default=None),
    user: dict = Depends(require_user),
    db: Session = Depends(get_db),
):
    if uid and user["role"] in ("admin", "superadmin"):
        target = get_user_by_uid(db, uid)
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        boards = db.query(Board).filter(Board.user_id == target.id).order_by(Board.sort_order).all()
        return [_board_to_response(b) for b in boards]

    u = get_user_by_uid(db, user["uid"])
    if not u:
        return []
    boards = db.query(Board).filter(Board.user_id == u.id).order_by(Board.sort_order).all()
    return [_board_to_response(b) for b in boards]

@router.get("/default", response_model=schemas.BoardResponse)
def get_default_board(user: dict = Depends(require_user), db: Session = Depends(get_db)):
    u = get_user_by_uid(db, user["uid"])
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    board = db.query(Board).filter(Board.user_id == u.id).order_by(Board.sort_order).first()
    if not board:
        raise HTTPException(status_code=404, detail="没有画板，请先创建一个")
    return _board_to_response(board)

@router.post("", response_model=schemas.BoardResponse, status_code=201)
def create_board(data: schemas.BoardCreate, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    u = get_user_by_uid(db, user["uid"])
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    b = Board(
        user_id=u.id,
        name=data.name,
        icon=data.icon,
        description=data.description,
        card_label=data.card_label,
        cards_label=data.cards_label,
        group_label=data.group_label,
        groups_label=data.groups_label,
        board_type=data.board_type,
        field_config=json.dumps(data.field_config, ensure_ascii=False),
        is_public=data.is_public,
        random_order=data.random_order,
        sort_order=data.sort_order,
    )
    db.add(b)
    db.flush()
    audit_log(db, user["username"], "create", "board", b.id, {"name": data.name})
    db.commit()
    db.refresh(b)
    return _board_to_response(b)

@router.get("/{board_id}", response_model=schemas.BoardResponse)
def get_board(board_id: int, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    board = db.query(Board).get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="画板不存在")
    require_board_owner(db, board_id, user)
    return _board_to_response(board)

@router.put("/{board_id}", response_model=schemas.BoardResponse)
def update_board(board_id: int, data: schemas.BoardUpdate, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    board = db.query(Board).get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="画板不存在")
    require_board_owner(db, board_id, user)
    changed = False
    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "field_config" and val is not None:
            setattr(board, field, json.dumps(val, ensure_ascii=False))
            changed = True
        elif val is not None:
            setattr(board, field, val)
            changed = True
    if changed:
        audit_log(db, user["username"], "update", "board", board_id, {"changed_fields": list(data.model_dump(exclude_unset=True).keys())})
    db.commit()
    db.refresh(board)
    return _board_to_response(board)

@router.delete("/{board_id}", status_code=204)
def delete_board(board_id: int, user: dict = Depends(require_user), db: Session = Depends(get_db)):
    board = db.query(Board).get(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="画板不存在")
    require_board_owner(db, board_id, user)
    user_boards = db.query(Board).filter(Board.user_id == board.user_id).count()
    if user_boards <= 1:
        raise HTTPException(status_code=400, detail="不能删除最后一个画板")
    info = {"name": board.name}
    db.delete(board)
    audit_log(db, user["username"], "delete", "board", board_id, info)
    db.commit()

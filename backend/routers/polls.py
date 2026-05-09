from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Poll
from schemas import PollCreate, PollUpdate, PollOut, OptionOut, VoteRequest, PollResult
from auth import get_current_user
from services import polls as svc

router = APIRouter(prefix="/api/v1/polls", tags=["polls"])


@router.post("")
def create(req: PollCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = svc.create_poll(db, req, user["user_id"])
    return {"code": 200, "message": "success", "data": _to_out(db, poll)}


@router.get("")
def list_all(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    polls = svc.list_all_polls(db)
    return {"code": 200, "message": "success", "data": [_to_out(db, p) for p in polls]}


@router.get("/mine")
def list_mine(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    polls = svc.list_my_polls(db, user["user_id"])
    return {"code": 200, "message": "success", "data": [_to_out(db, p) for p in polls]}


@router.get("/{poll_id}")
def get(poll_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = _get_or_404(db, poll_id)
    return {"code": 200, "message": "success", "data": _to_out(db, poll)}


@router.put("/{poll_id}")
def update(poll_id: int, req: PollUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = _get_or_404(db, poll_id)
    _check_owner(poll, user)
    poll = svc.update_poll(db, poll, req)
    return {"code": 200, "message": "success", "data": _to_out(db, poll)}


@router.delete("/{poll_id}")
def delete(poll_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = _get_or_404(db, poll_id)
    _check_owner(poll, user)
    svc.delete_poll(db, poll)
    return {"code": 200, "message": "success", "data": None}


@router.post("/{poll_id}/vote")
def vote(poll_id: int, req: VoteRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = _get_or_404(db, poll_id)
    if datetime.now(timezone.utc).isoformat() >= poll.expires_at:
        raise HTTPException(status_code=400, detail={"code": 2001, "message": "Poll has expired"})
    try:
        svc.vote(db, poll, user["user_id"], req.option_id)
    except svc.AlreadyVotedError:
        raise HTTPException(status_code=400, detail={"code": 2002, "message": "You have already voted"})
    except svc.InvalidOptionError:
        raise HTTPException(status_code=400, detail={"code": 2003, "message": "Invalid option"})
    return {"code": 200, "message": "success", "data": None}


@router.get("/{poll_id}/results")
def results(poll_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    poll = _get_or_404(db, poll_id)
    return {"code": 200, "message": "success", "data": svc.get_results(db, poll)}


def _to_out(db: Session, poll: Poll) -> dict:
    from models import Option
    options = db.query(Option).filter(Option.poll_id == poll.id).all()
    return {
        "id": poll.id,
        "title": poll.title,
        "creator_id": poll.creator_id,
        "expires_at": poll.expires_at,
        "created_at": poll.created_at,
        "updated_at": poll.updated_at,
        "options": [{"id": o.id, "text": o.text} for o in options],
    }


def _get_or_404(db: Session, poll_id: int) -> Poll:
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if poll is None:
        raise HTTPException(status_code=404, detail={"code": 2004, "message": "Poll not found"})
    return poll


def _check_owner(poll: Poll, user: dict):
    if poll.creator_id != user["user_id"]:
        raise HTTPException(status_code=403, detail={"code": 2005, "message": "Only the creator can modify this poll"})

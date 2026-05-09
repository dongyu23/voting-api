from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import Poll, Option, Vote
from schemas import PollCreate, PollUpdate, VoteRequest, PollResult, OptionResult


def create_poll(db: Session, data: PollCreate, creator_id: int) -> Poll:
    poll = Poll(
        title=data.title,
        creator_id=creator_id,
        expires_at=data.expires_at,
    )
    db.add(poll)
    db.flush()
    for opt in data.options:
        db.add(Option(poll_id=poll.id, text=opt.text))
    db.commit()
    db.refresh(poll)
    return poll


def get_poll(db: Session, poll_id: int) -> Poll | None:
    return db.query(Poll).filter(Poll.id == poll_id).first()


def list_all_polls(db: Session) -> list[Poll]:
    return db.query(Poll).order_by(Poll.created_at.desc()).all()


def list_my_polls(db: Session, user_id: int) -> list[Poll]:
    return db.query(Poll).filter(Poll.creator_id == user_id).order_by(Poll.created_at.desc()).all()


def update_poll(db: Session, poll: Poll, data: PollUpdate):
    now = datetime.now(timezone.utc).isoformat()
    if data.title is not None:
        poll.title = data.title
    if data.expires_at is not None:
        poll.expires_at = data.expires_at
    if data.options is not None:
        db.query(Option).filter(Option.poll_id == poll.id).delete()
        for opt in data.options:
            db.add(Option(poll_id=poll.id, text=opt.text))
    poll.updated_at = now
    db.commit()
    db.refresh(poll)
    return poll


def delete_poll(db: Session, poll: Poll):
    db.query(Vote).filter(Vote.poll_id == poll.id).delete()
    db.query(Option).filter(Option.poll_id == poll.id).delete()
    db.delete(poll)
    db.commit()


def vote(db: Session, poll: Poll, user_id: int, option_id: int):
    existing = db.query(Vote).filter(Vote.poll_id == poll.id, Vote.user_id == user_id).first()
    if existing is not None:
        raise AlreadyVotedError()
    option = db.query(Option).filter(Option.id == option_id, Option.poll_id == poll.id).first()
    if option is None:
        raise InvalidOptionError()
    v = Vote(poll_id=poll.id, option_id=option_id, user_id=user_id)
    db.add(v)
    db.commit()


def get_results(db: Session, poll: Poll) -> PollResult:
    options = db.query(Option).filter(Option.poll_id == poll.id).all()
    vote_counts = {}
    for opt in options:
        count = db.query(Vote).filter(Vote.option_id == opt.id).count()
        vote_counts[opt.id] = count
    total = sum(vote_counts.values())
    return PollResult(
        poll_id=poll.id,
        title=poll.title,
        total_votes=total,
        expired=datetime.now(timezone.utc).isoformat() >= poll.expires_at,
        options=[OptionResult(id=o.id, text=o.text, count=vote_counts.get(o.id, 0)) for o in options],
    )


class AlreadyVotedError(Exception):
    pass


class InvalidOptionError(Exception):
    pass

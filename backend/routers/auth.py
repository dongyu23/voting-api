from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserRegister, UserLogin
from services.auth import register as register_svc, login as login_svc

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
def register(req: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail={"code": 1002, "message": "Username already taken"})
    register_svc(db, req.username, req.password)
    return {"code": 200, "message": "success", "data": None}


@router.post("/login")
def login(req: UserLogin, db: Session = Depends(get_db)):
    token = login_svc(db, req.username, req.password)
    if token is None:
        raise HTTPException(status_code=401, detail={"code": 1001, "message": "Invalid username or password"})
    return {"code": 200, "message": "success", "data": {"access_token": token, "token_type": "bearer"}}

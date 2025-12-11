# backend/api.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .db import init_db, SessionLocal
from . import models, auth, crawler as crawler_mod, complaint_manager, ai_assistant
from sqlalchemy.orm import Session
import uvicorn
from typing import Optional, List
from .db import engine

app = FastAPI(title="AutoLegal Backend")

# initialize DB
init_db()

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ComplaintCreate(BaseModel):
    title: str
    description: str

# helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/register", response_model=dict)
def register_user(u: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == u.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username_taken")
    hashed = auth.hash_password(u.password)
    user = models.User(username=u.username, hashed_password=hashed, email=u.email, is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}

@app.post("/api/token", response_model=TokenResp)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = auth.create_access_token({"sub": str(user.id), "username": user.username, "is_admin": user.is_admin})
    return {"access_token": token}

def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    # For simplicity provide via Authorization header in real usage.
    # FastAPI dependency for full implementation would use OAuth2PasswordBearer
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")
    def inner(token: str = Depends(oauth2_scheme)):
        payload = auth.decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="invalid_token")
        user = db.query(models.User).get(int(payload.get("sub")))
        if not user:
            raise HTTPException(status_code=401, detail="user_not_found")
        return user
    return inner

# Crawler endpoint
@app.post("/api/crawl")
def crawl_url(url: str):
    res = crawler_mod.simple_crawl(url)
    return res

# Complaint endpoints
@app.post("/api/complaints")
def api_create_complaint(c: ComplaintCreate, token: str = Depends(get_current_user())):
    user = token
    comp = complaint_manager.create_complaint(user.id, c.title, c.description)
    return {"id": comp.id, "status": comp.status}

@app.get("/api/complaints")
def api_list_complaints(user_id: Optional[int] = None, token: str = Depends(get_current_user())):
    # admin may pass user_id to list others; normal user sees only theirs
    user = token
    if (not user.is_admin) and (user_id and user_id != user.id):
        raise HTTPException(status_code=403, detail="forbidden")
    uid = user_id if user_id else user.id
    comps = complaint_manager.list_complaints(user_id=uid)
    return [{"id": c.id, "title": c.title, "status": c.status, "created_at": str(c.created_at)} for c in comps]

@app.post("/api/complaints/{complaint_id}/status")
def api_update_status(complaint_id: int, status: str, token: str = Depends(get_current_user())):
    user = token
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="forbidden")
    updated = complaint_manager.update_complaint_status(complaint_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="not_found")
    return {"id": updated.id, "status": updated.status}

# AI assistant endpoint
@app.post("/api/ai")
def api_ai(query: str):
    # prefer OpenAI if key present else return local stub
    from .ai_assistant import ask_openai, local_stub
    if os.environ.get("OPENAI_API_KEY"):
        return ask_openai(query)
    return local_stub(query)

# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8001, reload=True)

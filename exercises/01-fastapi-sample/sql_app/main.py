from fastapi import Depends, FastAPI, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(x_api_token: str = Header(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_token(db, x_api_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return user

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db=db, user=user)
    return {"email": user.email, "id": user.id, "is_active": user.is_active, "api_token": user.api_token}

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)

@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/me/items/", response_model=List[schemas.Item])
def read_own_items(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = crud.get_user_items(db, user_id=current_user.id)
    return items

@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
import secrets
from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = user.password + "notreallyhashed"
    api_token = secrets.token_urlsafe(32)
    db_user = models.User(email=user.email, hashed_password=hashed_password, api_token=api_token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_token(db: Session, token: str):
    return db.query(models.User).filter(models.User.api_token == token).first()

def get_user_items(db: Session, user_id: int):
    return db.query(models.Item).filter(models.Item.owner_id == user_id).all()

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    
    # ユーザーを非アクティブにする
    user.is_active = False
    
    # 所有権を移す
    items = db.query(models.Item).filter(models.Item.owner_id == user_id).all()
    if items:
        new_owner = db.query(models.User).filter(models.User.is_active == True, models.User.id != user_id).order_by(models.User.id).first()
        if new_owner:
            for item in items:
                item.owner_id = new_owner.id
    
    db.commit()
    return user
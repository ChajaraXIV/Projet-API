from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, time, timedelta
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter
router = APIRouter()


class User(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    created_at: datetime = None
    updated_at: datetime = None


fake_db: List[User] = []


@router.get("/", response_model=List[User])
def get_users():
    return fake_db


@router.get("/{user_id}", response_model=User)
def get_user(user_id: UUID):
    for user in fake_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="user does not exist")


@router.post("/", response_model=User)
def create_user(user: User):
    fake_db.append(user)
    return user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: UUID, updated_user: User):
    for id, user in enumerate(fake_db):
        if user.id == user_id:
            fake_db[id] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="user does not exist")


@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: UUID):
    for id, user in enumerate(fake_db):
        if user.id == user_id:
            del fake_db[id]
            return {"message": "user deleted"}
    raise HTTPException(status_code=404, detail="user does not exist")

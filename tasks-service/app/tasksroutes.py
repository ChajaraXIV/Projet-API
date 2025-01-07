from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime, time, timedelta
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter


router = APIRouter()


class Task(BaseModel):
    id: UUID
    user_id: int
    content: str
    created_at: datetime = None
    completed: bool = False
    completed_at: datetime = None


fake_db: List[Task] = []


@router.get("/", response_model=List[Task])
def get_tasks():
    return fake_db


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: UUID):
    for task in fake_db:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task doest not exist")


@router.post("/", response_model=Task)
def create_task(task: Task):
    fake_db.append(task)
    return task


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: UUID, updated_task: Task):
    for id, task in enumerate(fake_db):
        if task.id == task_id:
            fake_db[id] = updated_task
            return updated_task
    raise HTTPException(status_code=404, detail="Task doest not exist")


@router.delete("/{task_id}", response_model=dict)
def delete_task(task_id: UUID):
    for id, task in enumerate(fake_db):
        if task.id == task_id:
            del fake_db[id]
            return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task doest not exist")

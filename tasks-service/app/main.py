from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, time, timedelta
from typing import Annotated
from uuid import UUID
import app.tasksroutes as tasksroutes
import app.usersroutes as usersroutes

app = FastAPI()

app.include_router(usersroutes.router, prefix="/users", tags=["Users"])
app.include_router(tasksroutes.router, prefix="/tasks", tags=["Tasks"])


@app.get("/")
def root():
    return {"message": "Welcome!"}

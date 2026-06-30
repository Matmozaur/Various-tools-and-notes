from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "user-service")

app = FastAPI(title="User Service")
users: dict[str, dict[str, str]] = {}


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=200)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/users")
def list_users() -> dict[str, object]:
    return {"users": [{"id": uid, **u} for uid, u in users.items()]}


@app.post("/users")
def create_user(payload: CreateUserRequest) -> dict[str, str]:
    user_id = str(uuid4())
    users[user_id] = {"name": payload.name, "email": payload.email}
    return {"id": user_id, "name": payload.name, "email": payload.email}


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict[str, str]:
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, **user}

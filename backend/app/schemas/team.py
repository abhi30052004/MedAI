"""Pydantic schemas for team endpoints."""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    name: str


class TeamMemberAdd(BaseModel):
    user_id: int


class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    id: int
    name: str
    members: List[TeamMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)

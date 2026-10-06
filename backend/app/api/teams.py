from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.team import Team, TeamMember
from app.schemas.team import TeamCreate, TeamResponse, TeamMemberAdd

router = APIRouter()

@router.get("/", response_model=List[TeamResponse])
def read_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    teams = db.query(Team).filter(Team.org_id == current_user.org_id).all()
    return teams

@router.post("/", response_model=TeamResponse)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin"))
):
    team = Team(name=team_in.name, org_id=current_user.org_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

@router.post("/{team_id}/members", response_model=TeamResponse)
def add_team_member(
    team_id: int,
    member_in: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin"))
):
    team = db.query(Team).filter(Team.id == team_id, Team.org_id == current_user.org_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    user = db.query(User).filter(User.id == member_in.user_id, User.org_id == current_user.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    existing_member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id).first()
    if not existing_member:
        member = TeamMember(team_id=team_id, user_id=user.id)
        db.add(member)
        db.commit()
        db.refresh(team)
        
    return team

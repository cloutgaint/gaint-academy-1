import hashlib
import secrets
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import Session as UserSession, User, UserRole, Role, RolePermission, Permission, now

SESSION_COOKIE="gaint_session"

def new_session_token():
    raw=secrets.token_urlsafe(48)
    return raw, hashlib.sha256(raw.encode()).hexdigest()

def token_hash(raw:str)->str:
    return hashlib.sha256(raw.encode()).hexdigest()

def current_user(session_token:str|None=Cookie(default=None,alias=SESSION_COOKIE),db:Session=Depends(get_db))->User:
    if not session_token: raise HTTPException(status_code=401,detail="Authentication required")
    session=db.scalar(select(UserSession).where(UserSession.token_hash==token_hash(session_token),UserSession.revoked_at.is_(None),UserSession.expires_at>now()))
    if not session: raise HTTPException(status_code=401,detail="Invalid or expired session")
    user=db.get(User,session.user_id)
    if not user or not user.is_active or user.tenant_id!=session.tenant_id: raise HTTPException(status_code=401,detail="Invalid session")
    return user

def permission_codes(db:Session,user:User)->list[str]:
    rows=db.execute(select(Permission.code).join(RolePermission,RolePermission.permission_id==Permission.id).join(Role,Role.id==RolePermission.role_id).join(UserRole,UserRole.role_id==Role.id).where(UserRole.user_id==user.id,UserRole.tenant_id==user.tenant_id)).scalars().all()
    return sorted(set(rows))

def role_codes(db:Session,user:User)->list[str]:
    rows=db.execute(select(Role.code).join(UserRole,UserRole.role_id==Role.id).where(UserRole.user_id==user.id,UserRole.tenant_id==user.tenant_id,Role.tenant_id==user.tenant_id)).scalars().all()
    return sorted(set(rows))

def role_scopes(db:Session,user:User)->list[dict[str,str|None]]:
    rows=db.execute(select(Role.code,UserRole.scope_type,UserRole.scope_id).join(UserRole,UserRole.role_id==Role.id).where(UserRole.user_id==user.id,UserRole.tenant_id==user.tenant_id,Role.tenant_id==user.tenant_id)).all()
    return [{"role":role,"scope_type":scope_type,"scope_id":scope_id} for role,scope_type,scope_id in rows]

def has_role(db:Session,user:User,code:str)->bool:
    return code in role_codes(db,user)

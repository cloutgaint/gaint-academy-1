from datetime import timedelta
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from redis import Redis
from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession
from app.db.session import get_db
from app.models.identity import User, Session, AuditEvent, Tenant, now
from app.core.security import verify_password, hash_password
from app.core.auth import SESSION_COOKIE, current_user, new_session_token, permission_codes, token_hash
from app.core.config import settings
from app.core.email import send_password_reset_otp

router=APIRouter(prefix="/auth",tags=["auth"])

class LoginIn(BaseModel):
    institution_code: str
    email: EmailStr
    password: str

class ForgotPasswordIn(BaseModel):
    institution_code: str
    email: EmailStr

class ResetPasswordIn(BaseModel):
    institution_code: str
    email: EmailStr
    otp: str=Field(min_length=6,max_length=6,pattern=r"^\d{6}$")
    new_password: str=Field(min_length=10,max_length=128)

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str=Field(min_length=10,max_length=128)

def _redis() -> Redis:
    return Redis.from_url(settings.redis_url,decode_responses=True)

def _reset_key(institution_code:str,email:str)->str:
    identity=f"{institution_code.strip().upper()}:{email.strip().lower()}".encode()
    return "auth:reset:"+hashlib.sha256(identity).hexdigest()

def _otp_hash(otp:str)->str:
    return hashlib.sha256(otp.encode()).hexdigest()

@router.post("/login")
def login(payload:LoginIn,request:Request,response:Response,db:DbSession=Depends(get_db)):
    tenant=db.scalar(select(Tenant).where(Tenant.code==payload.institution_code.strip().upper(),Tenant.status=="ACTIVE"))
    user=None if not tenant else db.scalar(select(User).where(User.tenant_id==tenant.id,User.email==payload.email.lower(),User.is_active.is_(True)))
    if not user or not verify_password(payload.password,user.password_hash):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    raw,digest=new_session_token()
    db.add(Session(tenant_id=user.tenant_id,user_id=user.id,token_hash=digest,expires_at=now()+timedelta(hours=settings.session_hours)))
    db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="auth.login",resource_type="user",resource_id=str(user.id),request_id=request.state.request_id))
    db.commit()
    response.set_cookie(SESSION_COOKIE,raw,httponly=True,secure=settings.cookie_secure,samesite="lax",max_age=settings.session_hours*3600,path="/")
    return {"data":{"user_id":str(user.id),"tenant_id":str(user.tenant_id),"email":user.email},"request_id":request.state.request_id}

@router.post("/forgot-password")
def forgot_password(payload:ForgotPasswordIn,request:Request,db:DbSession=Depends(get_db)):
    code=payload.institution_code.strip().upper(); email=payload.email.strip().lower()
    generic={"data":{"accepted":True,"message":"If the account exists, a reset code has been sent."},"request_id":request.state.request_id}
    tenant=db.scalar(select(Tenant).where(Tenant.code==code,Tenant.status=="ACTIVE"))
    user=None if not tenant else db.scalar(select(User).where(User.tenant_id==tenant.id,User.email==email,User.is_active.is_(True)))
    if not user:
        return generic
    redis=_redis(); key=_reset_key(code,email)
    throttle=key+":throttle"; hourly=key+":hour"
    if redis.exists(throttle):
        return generic
    count=redis.incr(hourly)
    if count==1: redis.expire(hourly,3600)
    if count>5:
        return generic
    otp=f"{secrets.randbelow(1_000_000):06d}"
    redis.hset(key,mapping={"otp_hash":_otp_hash(otp),"attempts":"0","user_id":str(user.id),"tenant_id":str(user.tenant_id)})
    redis.expire(key,settings.password_reset_otp_minutes*60)
    redis.setex(throttle,60,"1")
    try:
        send_password_reset_otp(user.email,otp)
    except Exception:
        redis.delete(key)
        if settings.app_env.lower() in {"production","staging"}:
            raise HTTPException(status_code=503,detail="Password recovery is temporarily unavailable")
        raise HTTPException(status_code=503,detail="Password reset email is not configured")
    db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="auth.password_reset_requested",resource_type="user",resource_id=str(user.id),request_id=request.state.request_id))
    db.commit()
    return generic

@router.post("/reset-password")
def reset_password(payload:ResetPasswordIn,request:Request,db:DbSession=Depends(get_db)):
    code=payload.institution_code.strip().upper(); email=payload.email.strip().lower()
    redis=_redis(); key=_reset_key(code,email); data=redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=400,detail="Invalid or expired reset code")
    attempts=int(data.get("attempts","0"))+1
    redis.hset(key,"attempts",attempts)
    if attempts>5:
        redis.delete(key)
        raise HTTPException(status_code=400,detail="Invalid or expired reset code")
    if not secrets.compare_digest(data.get("otp_hash",""),_otp_hash(payload.otp)):
        raise HTTPException(status_code=400,detail="Invalid or expired reset code")
    tenant=db.scalar(select(Tenant).where(Tenant.code==code,Tenant.status=="ACTIVE"))
    user=None if not tenant else db.scalar(select(User).where(User.tenant_id==tenant.id,User.email==email,User.is_active.is_(True)))
    if user and str(user.id)!=data.get("user_id"):
        user=None
    if not user:
        redis.delete(key)
        raise HTTPException(status_code=400,detail="Invalid or expired reset code")
    user.password_hash=hash_password(payload.new_password)
    db.execute(update(Session).where(Session.user_id==user.id,Session.revoked_at.is_(None)).values(revoked_at=now()))
    db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="auth.password_reset_completed",resource_type="user",resource_id=str(user.id),request_id=request.state.request_id))
    db.commit(); redis.delete(key)
    return {"data":{"reset":True},"request_id":request.state.request_id}

@router.post("/change-password")
def change_password(payload:ChangePasswordIn,request:Request,user:User=Depends(current_user),db:DbSession=Depends(get_db)):
    if not verify_password(payload.current_password,user.password_hash):
        raise HTTPException(status_code=400,detail="Current password is incorrect")
    if verify_password(payload.new_password,user.password_hash):
        raise HTTPException(status_code=400,detail="New password must be different")
    user.password_hash=hash_password(payload.new_password)
    raw=request.cookies.get(SESSION_COOKIE)
    current_digest=token_hash(raw) if raw else None
    q=update(Session).where(Session.user_id==user.id,Session.revoked_at.is_(None))
    if current_digest: q=q.where(Session.token_hash!=current_digest)
    db.execute(q.values(revoked_at=now()))
    db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="auth.password_changed",resource_type="user",resource_id=str(user.id),request_id=request.state.request_id))
    db.commit()
    return {"data":{"changed":True},"request_id":request.state.request_id}

@router.get("/me")
def me(request:Request,user:User=Depends(current_user),db:DbSession=Depends(get_db)):
    return {"data":{"user_id":str(user.id),"tenant_id":str(user.tenant_id),"email":user.email,"permissions":permission_codes(db,user)},"request_id":request.state.request_id}

@router.post("/logout")
def logout(request:Request,response:Response,session_token:str|None=None,user:User=Depends(current_user),db:DbSession=Depends(get_db)):
    raw=request.cookies.get(SESSION_COOKIE)
    if raw:
        session=db.scalar(select(Session).where(Session.token_hash==token_hash(raw),Session.user_id==user.id,Session.revoked_at.is_(None)))
        if session: session.revoked_at=now()
    db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="auth.logout",resource_type="user",resource_id=str(user.id),request_id=request.state.request_id))
    db.commit(); response.delete_cookie(SESSION_COOKIE,path="/")
    return {"data":{"logged_out":True},"request_id":request.state.request_id}

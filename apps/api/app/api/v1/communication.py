from datetime import datetime,timezone
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes,role_codes
from app.db.session import get_db
from app.models.identity import User,AuditEvent,Role,UserRole
from app.models.communication import Notice,Notification
router=APIRouter(tags=["communication"])
def req(db,u,p):
 if p not in permission_codes(db,u):raise HTTPException(403,"Permission denied")
ALLOWED_AUDIENCES={"ALL","STUDENT","PARENT","TEACHER","STAFF"}
class NoticeIn(BaseModel):title:str;body:str;audience:str="ALL"
@router.post("/notices",status_code=201)
def create_notice(p:NoticeIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"communication.notice.manage")
 audience=p.audience.upper()
 if audience not in ALLOWED_AUDIENCES:raise HTTPException(422,"Invalid notice audience")
 x=Notice(tenant_id=u.tenant_id,created_by=u.id,title=p.title,body=p.body,audience=audience);db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status}}
@router.get("/notices")
def notices(u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"communication.notice.view")
 roles=set(role_codes(db,u));audiences={"ALL"}|roles
 if roles&{"INSTITUTION_ADMIN","PRINCIPAL","GAINT_SUPER_ADMIN","CAMPUS_ADMIN"}:audiences=ALLOWED_AUDIENCES
 if "TEACHER" in roles:audiences.add("STAFF")
 rows=db.scalars(select(Notice).where(Notice.tenant_id==u.tenant_id,Notice.status=="PUBLISHED",Notice.audience.in_(audiences)).order_by(Notice.published_at.desc())).all();return {"data":[{"id":str(x.id),"title":x.title,"body":x.body,"audience":x.audience,"published_at":x.published_at} for x in rows]}
@router.post("/notices/{notice_id}/publish")
def publish(notice_id:UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"communication.notice.publish");x=db.scalar(select(Notice).where(Notice.id==notice_id,Notice.tenant_id==u.tenant_id))
 if not x:raise HTTPException(404,"Notice not found")
 if x.status!="DRAFT":raise HTTPException(409,"Notice is not in DRAFT state")
 x.status="PUBLISHED";x.published_at=datetime.now(timezone.utc)
 if x.audience=="ALL":
  recipients=db.scalars(select(User).where(User.tenant_id==u.tenant_id,User.is_active.is_(True))).all()
 else:
  recipient_ids=select(UserRole.user_id).join(Role,Role.id==UserRole.role_id).where(UserRole.tenant_id==u.tenant_id,Role.tenant_id==u.tenant_id,Role.code==x.audience)
  if x.audience=="STAFF":recipient_ids=select(UserRole.user_id).join(Role,Role.id==UserRole.role_id).where(UserRole.tenant_id==u.tenant_id,Role.tenant_id==u.tenant_id,Role.code.in_({"TEACHER","HR","ACCOUNTS","TRANSPORT_ADMIN","LIBRARIAN","HOSTEL_ADMIN","ASSET_ADMIN"}))
  recipients=db.scalars(select(User).where(User.tenant_id==u.tenant_id,User.is_active.is_(True),User.id.in_(recipient_ids))).all()
 for recipient in recipients:db.add(Notification(tenant_id=u.tenant_id,user_id=recipient.id,title=x.title,body=x.body))
 db.add(AuditEvent(tenant_id=u.tenant_id,user_id=u.id,action="notice.published",resource_type="notice",resource_id=str(x.id)));db.commit();return {"data":{"id":str(x.id),"status":x.status}}
@router.get("/notifications")
def notifications(u:User=Depends(current_user),db:Session=Depends(get_db)):
 rows=db.scalars(select(Notification).where(Notification.tenant_id==u.tenant_id,Notification.user_id==u.id).order_by(Notification.created_at.desc())).all();return {"data":[{"id":str(x.id),"title":x.title,"body":x.body,"status":x.status} for x in rows]}
@router.post("/notifications/{notification_id}/read")
def read(notification_id:UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
 x=db.scalar(select(Notification).where(Notification.id==notification_id,Notification.tenant_id==u.tenant_id,Notification.user_id==u.id))
 if not x:raise HTTPException(404,"Notification not found")
 x.status="READ";db.commit();return {"data":{"id":str(x.id),"status":x.status}}

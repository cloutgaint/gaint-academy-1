from datetime import date,time
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes,has_role,teacher_section_ids,require_teacher_section,linked_student_ids,scoped_student_id
from app.db.session import get_db
from app.models.identity import User,AuditEvent
from app.models.academics import Section,Enrollment,Student
from app.models.attendance import TimetableSlot,AttendanceSession,AttendanceRecord
from app.models.people import Guardian,StudentGuardian
from app.models.communication import Notification
router=APIRouter(tags=["attendance"])
def require(db,u,c):
 if c not in permission_codes(db,u): raise HTTPException(403,"Permission denied")
class SlotIn(BaseModel): section_id:UUID;staff_id:UUID|None=None;subject_name:str;weekday:str;start_time:time;end_time:time
@router.post("/timetable",status_code=201)
def slot(p:SlotIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"timetable.slot.manage");sec=db.scalar(select(Section).where(Section.id==p.section_id,Section.tenant_id==u.tenant_id))
 if not sec: raise HTTPException(404,"Section not found")
 x=TimetableSlot(tenant_id=u.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id)}}
@router.get("/timetable")
def slots(section_id:UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"timetable.slot.view");require_teacher_section(db,u,section_id)
 rows=db.scalars(select(TimetableSlot).where(TimetableSlot.tenant_id==u.tenant_id,TimetableSlot.section_id==section_id)).all()
 return {"data":[{"id":str(x.id),"subject_name":x.subject_name,"weekday":x.weekday,"start_time":str(x.start_time),"end_time":str(x.end_time)} for x in rows]}

@router.get("/attendance/records")
def attendance_records(student_id:UUID|None=None,u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"attendance.session.view")
 allowed=None
 if has_role(db,u,"PARENT"):allowed=linked_student_ids(db,u)
 if has_role(db,u,"STUDENT"):
  own=scoped_student_id(db,u);allowed=set() if not own else {own}
 if allowed is not None:
  if student_id and student_id not in allowed:raise HTTPException(404,"Student not found")
  ids={student_id} if student_id else allowed
 else:
  ids={student_id} if student_id else None
 q=select(AttendanceRecord,AttendanceSession).join(AttendanceSession,AttendanceSession.id==AttendanceRecord.session_id).where(AttendanceRecord.tenant_id==u.tenant_id,AttendanceSession.tenant_id==u.tenant_id,AttendanceSession.status=="SUBMITTED")
 if ids is not None:
  if not ids:return {"data":[]}
  q=q.where(AttendanceRecord.student_id.in_(ids))
 rows=db.execute(q.order_by(AttendanceSession.attendance_date.desc())).all()
 return {"data":[{"student_id":str(r.student_id),"attendance_date":str(s.attendance_date),"status":r.status,"remark":r.remark} for r,s in rows]}

class AttendanceIn(BaseModel): section_id:UUID;attendance_date:date
@router.post("/attendance/sessions",status_code=201)
def create_session(p:AttendanceIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"attendance.session.create");require_teacher_section(db,u,p.section_id);sec=db.scalar(select(Section).where(Section.id==p.section_id,Section.tenant_id==u.tenant_id))
 if not sec: raise HTTPException(404,"Section not found")
 x=AttendanceSession(tenant_id=u.tenant_id,created_by=u.id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status}}
class RecordIn(BaseModel): student_id:UUID;status:str;remark:str|None=None
@router.put("/attendance/sessions/{session_id}/records")
def mark(session_id:UUID,records:list[RecordIn],u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"attendance.record.mark");s=db.scalar(select(AttendanceSession).where(AttendanceSession.id==session_id,AttendanceSession.tenant_id==u.tenant_id,AttendanceSession.status=="DRAFT"))
 if not s: raise HTTPException(404,"Attendance session not found")
 require_teacher_section(db,u,s.section_id)
 valid={"PRESENT","ABSENT","LATE","EXCUSED"}
 for r in records:
  if r.status not in valid: raise HTTPException(422,"Invalid attendance status")
  enrolled=db.scalar(select(Enrollment).where(Enrollment.tenant_id==u.tenant_id,Enrollment.section_id==s.section_id,Enrollment.student_id==r.student_id,Enrollment.status=="ACTIVE"))
  if not enrolled: raise HTTPException(404,"Student enrollment not found")
  x=db.scalar(select(AttendanceRecord).where(AttendanceRecord.session_id==s.id,AttendanceRecord.student_id==r.student_id))
  if x:x.status=r.status;x.remark=r.remark
  else:db.add(AttendanceRecord(tenant_id=u.tenant_id,session_id=s.id,student_id=r.student_id,status=r.status,remark=r.remark))
 db.commit();return {"data":{"saved":len(records)}}
@router.post("/attendance/sessions/{session_id}/submit")
def submit(session_id:UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
 require(db,u,"attendance.session.submit");s=db.scalar(select(AttendanceSession).where(AttendanceSession.id==session_id,AttendanceSession.tenant_id==u.tenant_id))
 if not s:raise HTTPException(404,"Attendance session not found")
 require_teacher_section(db,u,s.section_id)
 if s.status!="DRAFT":raise HTTPException(409,"Attendance session is not in DRAFT state")
 enrolled_count=len(db.scalars(select(Enrollment).where(Enrollment.tenant_id==u.tenant_id,Enrollment.section_id==s.section_id,Enrollment.status=="ACTIVE")).all())
 marked_count=len(db.scalars(select(AttendanceRecord).where(AttendanceRecord.tenant_id==u.tenant_id,AttendanceRecord.session_id==s.id)).all())
 if marked_count!=enrolled_count:raise HTTPException(409,"Attendance is incomplete for the active section roster")
 absent_ids=db.scalars(select(AttendanceRecord.student_id).where(AttendanceRecord.tenant_id==u.tenant_id,AttendanceRecord.session_id==s.id,AttendanceRecord.status=="ABSENT")).all()
 if absent_ids:
  guardians=db.execute(select(StudentGuardian.student_id,Guardian.user_id).join(Guardian,Guardian.id==StudentGuardian.guardian_id).where(StudentGuardian.tenant_id==u.tenant_id,StudentGuardian.student_id.in_(absent_ids),Guardian.tenant_id==u.tenant_id,Guardian.user_id.is_not(None))).all()
  for student_id,user_id in guardians:db.add(Notification(tenant_id=u.tenant_id,user_id=user_id,title="Attendance alert",body=f"Student {student_id} was marked absent on {s.attendance_date}."))
 s.status="SUBMITTED";db.add(AuditEvent(tenant_id=u.tenant_id,user_id=u.id,action="attendance.submitted",resource_type="attendance_session",resource_id=str(s.id)));db.commit();return {"data":{"id":str(s.id),"status":s.status}}

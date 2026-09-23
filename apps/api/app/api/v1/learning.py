from datetime import datetime
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes,has_role,linked_student_ids,require_linked_student,teacher_section_ids,require_teacher_section,student_section_ids,require_self_student
from app.db.session import get_db
from app.models.identity import User,AuditEvent
from app.models.academics import Section,Enrollment
from app.models.learning import Course,Assignment,Assessment,AssessmentMark,Submission
router=APIRouter(tags=["learning"])
def req(db,u,p):
 if p not in permission_codes(db,u):raise HTTPException(403,"Permission denied")
class CourseIn(BaseModel):section_id:UUID;teacher_id:UUID|None=None;name:str
@router.post("/courses",status_code=201)
def course(p:CourseIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"learning.course.manage");sec=db.scalar(select(Section).where(Section.id==p.section_id,Section.tenant_id==u.tenant_id))
 if not sec:raise HTTPException(404,"Section not found")
 require_teacher_section(db,u,p.section_id)
 x=Course(tenant_id=u.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"name":x.name}}
@router.get("/courses")
def courses(u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"learning.course.view")
 q=select(Course).where(Course.tenant_id==u.tenant_id)
 if has_role(db,u,"TEACHER"):
  sections=teacher_section_ids(db,u)
  if not sections:return {"data":[]}
  q=q.where(Course.section_id.in_(sections))
 if has_role(db,u,"STUDENT"):
  sections=student_section_ids(db,u)
  if not sections:return {"data":[]}
  q=q.where(Course.section_id.in_(sections))
 if has_role(db,u,"PARENT"):
  ids=linked_student_ids(db,u)
  if not ids:return {"data":[]}
  section_ids=select(Enrollment.section_id).where(Enrollment.tenant_id==u.tenant_id,Enrollment.student_id.in_(ids),Enrollment.status=="ACTIVE")
  q=q.where(Course.section_id.in_(section_ids))
 rows=db.scalars(q).all();return {"data":[{"id":str(x.id),"name":x.name,"section_id":str(x.section_id),"status":x.status} for x in rows]}
class AssignmentIn(BaseModel):course_id:UUID;title:str;instructions:str|None=None;max_marks:int=100;due_at:datetime|None=None
@router.post("/assignments",status_code=201)
def assignment(p:AssignmentIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"learning.assignment.manage");c=db.scalar(select(Course).where(Course.id==p.course_id,Course.tenant_id==u.tenant_id))
 if not c:raise HTTPException(404,"Course not found")
 require_teacher_section(db,u,c.section_id)
 x=Assignment(tenant_id=u.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status}}
class AssessmentIn(BaseModel):course_id:UUID;name:str;max_marks:int=100
@router.post("/assessments",status_code=201)
def assessment(p:AssessmentIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"assessment.manage");c=db.scalar(select(Course).where(Course.id==p.course_id,Course.tenant_id==u.tenant_id))
 if not c:raise HTTPException(404,"Course not found")
 require_teacher_section(db,u,c.section_id)
 x=Assessment(tenant_id=u.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status}}
class MarkIn(BaseModel):student_id:UUID;marks:int
@router.put("/assessments/{assessment_id}/marks")
def marks(assessment_id:UUID,rows:list[MarkIn],u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"assessment.marks.manage");a=db.scalar(select(Assessment).where(Assessment.id==assessment_id,Assessment.tenant_id==u.tenant_id))
 if not a:raise HTTPException(404,"Assessment not found")
 course=db.scalar(select(Course).where(Course.id==a.course_id,Course.tenant_id==u.tenant_id))
 if not course:raise HTTPException(404,"Course not found")
 require_teacher_section(db,u,course.section_id)
 for r in rows:
  enrolled=db.scalar(select(Enrollment).where(Enrollment.tenant_id==u.tenant_id,Enrollment.section_id==course.section_id,Enrollment.student_id==r.student_id,Enrollment.status=="ACTIVE"))
  if not enrolled:raise HTTPException(422,"Student is not actively enrolled in the course section")
  if r.marks<0 or r.marks>a.max_marks:raise HTTPException(422,"Marks outside assessment range")
  x=db.scalar(select(AssessmentMark).where(AssessmentMark.tenant_id==u.tenant_id,AssessmentMark.assessment_id==a.id,AssessmentMark.student_id==r.student_id))
  if x:x.marks=r.marks
  else:db.add(AssessmentMark(tenant_id=u.tenant_id,assessment_id=a.id,student_id=r.student_id,marks=r.marks))
 db.commit();return {"data":{"saved":len(rows)}}
class SubmissionIn(BaseModel):student_id:UUID;content:str
@router.post("/assignments/{assignment_id}/submissions",status_code=201)
def submit_assignment(assignment_id:UUID,p:SubmissionIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"learning.submission.create");require_linked_student(db,u,p.student_id);require_self_student(db,u,p.student_id);a=db.scalar(select(Assignment).where(Assignment.id==assignment_id,Assignment.tenant_id==u.tenant_id));c=None if not a else db.scalar(select(Course).where(Course.id==a.course_id,Course.tenant_id==u.tenant_id))
 if not a or not c:raise HTTPException(404,"Assignment not found")
 enrolled=db.scalar(select(Enrollment).where(Enrollment.tenant_id==u.tenant_id,Enrollment.section_id==c.section_id,Enrollment.student_id==p.student_id,Enrollment.status=="ACTIVE"))
 if not enrolled:raise HTTPException(422,"Student is not actively enrolled in the course section")
 x=Submission(tenant_id=u.tenant_id,assignment_id=a.id,student_id=p.student_id,content=p.content);db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status}}
@router.post("/assessments/{assessment_id}/publish")
def publish(assessment_id:UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"assessment.publish");a=db.scalar(select(Assessment).where(Assessment.id==assessment_id,Assessment.tenant_id==u.tenant_id))
 if not a:raise HTTPException(404,"Assessment not found")
 course=db.scalar(select(Course).where(Course.id==a.course_id,Course.tenant_id==u.tenant_id))
 if not course:raise HTTPException(404,"Course not found")
 require_teacher_section(db,u,course.section_id)
 if a.status!="DRAFT":raise HTTPException(409,"Assessment is not in DRAFT state")
 a.status="PUBLISHED";db.query(AssessmentMark).filter(AssessmentMark.tenant_id==u.tenant_id,AssessmentMark.assessment_id==a.id).update({"status":"PUBLISHED"});db.add(AuditEvent(tenant_id=u.tenant_id,user_id=u.id,action="assessment.published",resource_type="assessment",resource_id=str(a.id)));db.commit();return {"data":{"id":str(a.id),"status":a.status}}

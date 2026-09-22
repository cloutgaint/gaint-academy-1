from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes,has_role
from app.db.session import get_db
from app.models.identity import User
from app.models.people import Guardian,StudentGuardian
from app.models.academics import Student,Enrollment,AcademicYear,AcademicClass,Section
router=APIRouter(prefix="/students",tags=["students"])
def require(db,user,code):
    if code not in permission_codes(db,user): raise HTTPException(403,"Permission denied")
def parent_student_ids(db,user):
    if not has_role(db,user,"PARENT"): return None
    return select(StudentGuardian.student_id).join(Guardian,Guardian.id==StudentGuardian.guardian_id).where(StudentGuardian.tenant_id==user.tenant_id,Guardian.tenant_id==user.tenant_id,Guardian.user_id==user.id)
class StudentIn(BaseModel): admission_no:str; first_name:str; last_name:str|None=None; email:EmailStr|None=None
class EnrollIn(BaseModel): academic_year_id:UUID; class_id:UUID; section_id:UUID
@router.get("")
def list_students(user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.view")
    q=select(Student).where(Student.tenant_id==user.tenant_id)
    allowed=parent_student_ids(db,user)
    if allowed is not None: q=q.where(Student.id.in_(allowed))
    rows=db.scalars(q.order_by(Student.created_at.desc())).all()
    return {"data":[{"id":str(x.id),"admission_no":x.admission_no,"name":(x.first_name+" "+(x.last_name or "")).strip(),"email":x.email,"status":x.status} for x in rows]}
@router.post("",status_code=201)
def create_student(p:StudentIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.create"); x=Student(tenant_id=user.tenant_id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return {"data":{"id":str(x.id),"admission_no":x.admission_no}}
@router.get("/{student_id}")
def student(student_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.view")
    q=select(Student).where(Student.id==student_id,Student.tenant_id==user.tenant_id)
    allowed=parent_student_ids(db,user)
    if allowed is not None: q=q.where(Student.id.in_(allowed))
    x=db.scalar(q)
    if not x: raise HTTPException(404,"Student not found")
    enroll=db.scalar(select(Enrollment).where(Enrollment.student_id==x.id,Enrollment.tenant_id==user.tenant_id,Enrollment.status=="ACTIVE"))
    return {"data":{"id":str(x.id),"admission_no":x.admission_no,"first_name":x.first_name,"last_name":x.last_name,"email":x.email,"status":x.status,"enrollment":None if not enroll else {"academic_year_id":str(enroll.academic_year_id),"class_id":str(enroll.class_id),"section_id":str(enroll.section_id)}}}
@router.post("/{student_id}/enroll",status_code=201)
def enroll(student_id:UUID,p:EnrollIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"academics.setup.admin")
    student=db.scalar(select(Student).where(Student.id==student_id,Student.tenant_id==user.tenant_id))
    year=db.scalar(select(AcademicYear).where(AcademicYear.id==p.academic_year_id,AcademicYear.tenant_id==user.tenant_id))
    cls=db.scalar(select(AcademicClass).where(AcademicClass.id==p.class_id,AcademicClass.tenant_id==user.tenant_id,AcademicClass.academic_year_id==p.academic_year_id))
    sec=db.scalar(select(Section).where(Section.id==p.section_id,Section.tenant_id==user.tenant_id,Section.class_id==p.class_id))
    if not all([student,year,cls,sec]): raise HTTPException(404,"Enrollment resource not found")
    x=Enrollment(tenant_id=user.tenant_id,student_id=student_id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return {"data":{"id":str(x.id),"status":x.status}}

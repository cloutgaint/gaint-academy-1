from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes
from app.core.security import hash_password
from app.db.session import get_db
from app.models.identity import User,Role,UserRole
from app.models.academics import Student,Section
from app.models.people import Guardian,StudentGuardian,Staff,TeacherAssignment
router=APIRouter(tags=["people"])
def require(db,user,code):
    if code not in permission_codes(db,user): raise HTTPException(403,"Permission denied")
class GuardianIn(BaseModel): name:str; phone:str; email:EmailStr|None=None; relationship:str="PARENT"; is_primary:bool=True
@router.post("/students/{student_id}/guardians",status_code=201)
def add_guardian(student_id:UUID,p:GuardianIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.create")
    student=db.scalar(select(Student).where(Student.id==student_id,Student.tenant_id==user.tenant_id))
    if not student: raise HTTPException(404,"Student not found")
    guardian=db.scalar(select(Guardian).where(Guardian.tenant_id==user.tenant_id,Guardian.phone==p.phone))
    if not guardian: guardian=Guardian(tenant_id=user.tenant_id,name=p.name,phone=p.phone,email=p.email);db.add(guardian);db.flush()
    link=db.scalar(select(StudentGuardian).where(StudentGuardian.tenant_id==user.tenant_id,StudentGuardian.student_id==student.id,StudentGuardian.guardian_id==guardian.id))
    if not link:
        link=StudentGuardian(tenant_id=user.tenant_id,student_id=student.id,guardian_id=guardian.id,relationship=p.relationship,is_primary=p.is_primary);db.add(link)
    db.commit()
    return {"data":{"guardian_id":str(guardian.id),"relationship":link.relationship,"user_id":None if not guardian.user_id else str(guardian.user_id)}}
@router.get("/students/{student_id}/guardians")
def list_guardians(student_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.view")
    student=db.scalar(select(Student).where(Student.id==student_id,Student.tenant_id==user.tenant_id))
    if not student: raise HTTPException(404,"Student not found")
    rows=db.execute(select(Guardian,StudentGuardian).join(StudentGuardian,StudentGuardian.guardian_id==Guardian.id).where(StudentGuardian.tenant_id==user.tenant_id,StudentGuardian.student_id==student.id)).all()
    return {"data":[{"guardian_id":str(g.id),"name":g.name,"phone":g.phone,"email":g.email,"relationship":link.relationship,"is_primary":link.is_primary,"user_id":None if not g.user_id else str(g.user_id)} for g,link in rows]}
class GuardianUserLinkIn(BaseModel):user_id:UUID
@router.put("/guardians/{guardian_id}/user-link")
def link_guardian_user(guardian_id:UUID,p:GuardianUserLinkIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"students.student.create");guardian=db.scalar(select(Guardian).where(Guardian.id==guardian_id,Guardian.tenant_id==user.tenant_id));target=db.scalar(select(User).where(User.id==p.user_id,User.tenant_id==user.tenant_id,User.is_active.is_(True)))
    if not guardian or not target:raise HTTPException(404,"Guardian or user not found")
    guardian.user_id=target.id;db.commit();return {"data":{"guardian_id":str(guardian.id),"user_id":str(target.id)}}
class ParentAccountIn(BaseModel): email:EmailStr; password:str
@router.post("/guardians/{guardian_id}/parent-account",status_code=201)
def create_parent_account(guardian_id:UUID,p:ParentAccountIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"users.user.create")
    guardian=db.scalar(select(Guardian).where(Guardian.id==guardian_id,Guardian.tenant_id==user.tenant_id))
    if not guardian: raise HTTPException(404,"Guardian not found")
    if guardian.user_id: raise HTTPException(409,"Guardian already has a user account")
    email=p.email.lower()
    if len(p.password)<10: raise HTTPException(422,"Password must be at least 10 characters")
    if db.scalar(select(User).where(User.tenant_id==user.tenant_id,User.email==email)): raise HTTPException(409,"Email already exists")
    role=db.scalar(select(Role).where(Role.tenant_id==user.tenant_id,Role.code=="PARENT"))
    if not role:
        role=Role(tenant_id=user.tenant_id,code="PARENT",name="Parent");db.add(role);db.flush()
    target=User(tenant_id=user.tenant_id,email=email,password_hash=hash_password(p.password));db.add(target);db.flush()
    db.add(UserRole(tenant_id=user.tenant_id,user_id=target.id,role_id=role.id,scope_type="GUARDIAN",scope_id=str(guardian.id)))
    guardian.user_id=target.id;guardian.email=email;db.commit()
    return {"data":{"user_id":str(target.id),"guardian_id":str(guardian.id),"email":target.email,"role":"PARENT"}}
class StaffIn(BaseModel): employee_no:str; name:str; email:EmailStr|None=None; designation:str|None=None
@router.get("/staff")
def staff_list(user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"staff.staff.view"); rows=db.scalars(select(Staff).where(Staff.tenant_id==user.tenant_id)).all()
    return {"data":[{"id":str(x.id),"employee_no":x.employee_no,"name":x.name,"designation":x.designation,"status":x.status} for x in rows]}
@router.post("/staff",status_code=201)
def staff_create(p:StaffIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"staff.staff.create");x=Staff(tenant_id=user.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"employee_no":x.employee_no}}
class AssignIn(BaseModel): section_id:UUID; assignment_type:str="CLASS_TEACHER"
@router.post("/staff/{staff_id}/assignments",status_code=201)
def assign(staff_id:UUID,p:AssignIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"academics.setup.admin")
    staff=db.scalar(select(Staff).where(Staff.id==staff_id,Staff.tenant_id==user.tenant_id));section=db.scalar(select(Section).where(Section.id==p.section_id,Section.tenant_id==user.tenant_id))
    if not staff or not section: raise HTTPException(404,"Assignment resource not found")
    x=TeacherAssignment(tenant_id=user.tenant_id,staff_id=staff.id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id)}}

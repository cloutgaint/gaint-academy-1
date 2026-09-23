from datetime import date
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes
from app.db.session import get_db
from app.models.identity import User,AuditEvent
from app.models.academics import AcademicYear,AcademicClass,Section
router=APIRouter(prefix="/academics",tags=["academics"])
def require(db,user,code):
    if code not in permission_codes(db,user): raise HTTPException(status_code=403,detail="Permission denied")
class YearIn(BaseModel): name:str; start_date:date; end_date:date
class ClassIn(BaseModel): academic_year_id:UUID; name:str
class SectionIn(BaseModel): class_id:UUID; name:str
@router.get("/years")
def years(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return {"data":[{"id":str(x.id),"name":x.name,"status":x.status} for x in db.scalars(select(AcademicYear).where(AcademicYear.tenant_id==user.tenant_id)).all()]}
@router.post("/years",status_code=201)
def create_year(p:YearIn,r:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"academics.setup.admin"); x=AcademicYear(tenant_id=user.tenant_id,**p.model_dump()); db.add(x); db.flush(); db.add(AuditEvent(tenant_id=user.tenant_id,user_id=user.id,action="academics.year.create",resource_type="academic_year",resource_id=str(x.id),request_id=r.state.request_id)); db.commit(); return {"data":{"id":str(x.id),"name":x.name}}
@router.get("/classes")
def classes(academic_year_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(AcademicClass).where(AcademicClass.tenant_id==user.tenant_id,AcademicClass.academic_year_id==academic_year_id)).all()
    return {"data":[{"id":str(x.id),"name":x.name,"academic_year_id":str(x.academic_year_id)} for x in rows]}

@router.post("/classes",status_code=201)
def create_class(p:ClassIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"academics.setup.admin"); year=db.scalar(select(AcademicYear).where(AcademicYear.id==p.academic_year_id,AcademicYear.tenant_id==user.tenant_id))
    if not year: raise HTTPException(404,"Academic year not found")
    x=AcademicClass(tenant_id=user.tenant_id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return {"data":{"id":str(x.id),"name":x.name}}
@router.get("/sections")
def sections(class_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Section).where(Section.tenant_id==user.tenant_id,Section.class_id==class_id)).all()
    return {"data":[{"id":str(x.id),"name":x.name,"class_id":str(x.class_id)} for x in rows]}

@router.post("/sections",status_code=201)
def create_section(p:SectionIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    require(db,user,"academics.setup.admin"); cls=db.scalar(select(AcademicClass).where(AcademicClass.id==p.class_id,AcademicClass.tenant_id==user.tenant_id))
    if not cls: raise HTTPException(404,"Class not found")
    x=Section(tenant_id=user.tenant_id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return {"data":{"id":str(x.id),"name":x.name}}

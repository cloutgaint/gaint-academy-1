from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.auth import current_user, permission_codes, role_codes
from app.db.session import get_db
from app.models.identity import User
from app.models.academics import Student
from app.models.people import Staff, Guardian, StudentGuardian
from app.models.attendance import AttendanceSession
from app.models.finance import Invoice
from app.models.communication import Notice

router=APIRouter(prefix="/dashboard",tags=["dashboard"])

def count(db,model,tenant_id,*extra):
    return db.scalar(select(func.count()).select_from(model).where(model.tenant_id==tenant_id,*extra)) or 0

@router.get("/summary")
def summary(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    permissions=permission_codes(db,user); roles=role_codes(db,user); parent="PARENT" in roles
    if parent:
        linked=db.scalars(select(Student.id).join(StudentGuardian,StudentGuardian.student_id==Student.id).join(Guardian,Guardian.id==StudentGuardian.guardian_id).where(Student.tenant_id==user.tenant_id,StudentGuardian.tenant_id==user.tenant_id,Guardian.tenant_id==user.tenant_id,Guardian.user_id==user.id)).all()
        student_count=len(set(linked))
        invoice_count=0 if not linked else count(db,Invoice,user.tenant_id,Invoice.student_id.in_(linked),Invoice.status!="PAID")
        metrics=[
            {"label":"Linked children","value":student_count,"href":"/students"},
            {"label":"Open invoices","value":invoice_count,"href":"/finance"},
            {"label":"Published notices","value":count(db,Notice,user.tenant_id,Notice.status=="PUBLISHED"),"href":"/communication"},
            {"label":"Role","value":"PARENT / GUARDIAN","href":None},
        ]
        heading="Your family overview"; description="A summary of your linked students and current academy activity."
    else:
        metrics=[
            {"label":"Active students","value":count(db,Student,user.tenant_id,Student.status=="ACTIVE"),"href":"/students"},
            {"label":"Active staff","value":count(db,Staff,user.tenant_id,Staff.status=="ACTIVE"),"href":"/staff"},
            {"label":"Attendance sessions","value":count(db,AttendanceSession,user.tenant_id),"href":"/attendance"},
            {"label":"Open invoices","value":count(db,Invoice,user.tenant_id,Invoice.status!="PAID"),"href":"/finance"},
        ]
        heading="Academy overview"; description="Current operational indicators for your institution."
    return {"data":{"tenant_id":str(user.tenant_id),"email":user.email,"platform":"ONLINE","tenant_isolation":"ENABLED","rbac":"ENABLED" if permissions else "NO_PERMISSIONS","audit":"ENABLED","heading":heading,"description":description,"metrics":metrics},"request_id":request.state.request_id}

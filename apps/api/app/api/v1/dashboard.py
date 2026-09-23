from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.auth import current_user, permission_codes, role_codes, scoped_student_id, teacher_section_ids
from app.db.session import get_db
from app.models.identity import User
from app.models.academics import Student
from app.models.people import Staff, Guardian, StudentGuardian
from app.models.attendance import AttendanceSession, AttendanceRecord
from app.models.finance import Invoice
from app.models.communication import Notice

router=APIRouter(prefix="/dashboard",tags=["dashboard"])

def count(db,model,tenant_id,*extra):
    return db.scalar(select(func.count()).select_from(model).where(model.tenant_id==tenant_id,*extra)) or 0

@router.get("/summary")
def summary(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    permissions=permission_codes(db,user); roles=role_codes(db,user); parent="PARENT" in roles
    student_role="STUDENT" in roles
    if student_role:
        own=scoped_student_id(db,user)
        submitted=0; present=0
        if own:
            submitted=db.scalar(select(func.count()).select_from(AttendanceRecord).join(AttendanceSession,AttendanceSession.id==AttendanceRecord.session_id).where(AttendanceRecord.tenant_id==user.tenant_id,AttendanceRecord.student_id==own,AttendanceSession.tenant_id==user.tenant_id,AttendanceSession.status=="SUBMITTED")) or 0
            present=db.scalar(select(func.count()).select_from(AttendanceRecord).join(AttendanceSession,AttendanceSession.id==AttendanceRecord.session_id).where(AttendanceRecord.tenant_id==user.tenant_id,AttendanceRecord.student_id==own,AttendanceRecord.status=="PRESENT",AttendanceSession.tenant_id==user.tenant_id,AttendanceSession.status=="SUBMITTED")) or 0
        attendance_rate="—" if not submitted else f"{round((present/submitted)*100)}%"
        metrics=[
            {"label":"My profile","value":"Linked" if own else "Not linked","href":"/students"},
            {"label":"Attendance","value":attendance_rate,"href":"/attendance"},
            {"label":"Learning","value":"My courses","href":"/learning"},
            {"label":"Role","value":"STUDENT","href":None},
        ]
        heading="Your student workspace"; description="Your academic profile, learning and attendance workspace."
    elif parent:
        linked=db.scalars(select(Student.id).join(StudentGuardian,StudentGuardian.student_id==Student.id).join(Guardian,Guardian.id==StudentGuardian.guardian_id).where(Student.tenant_id==user.tenant_id,StudentGuardian.tenant_id==user.tenant_id,Guardian.tenant_id==user.tenant_id,Guardian.user_id==user.id)).all()
        student_count=len(set(linked))
        invoice_count=0 if not linked else count(db,Invoice,user.tenant_id,Invoice.student_id.in_(linked),Invoice.status!="PAID")
        attendance_total=0; attendance_present=0
        if linked:
            attendance_total=db.scalar(select(func.count()).select_from(AttendanceRecord).join(AttendanceSession,AttendanceSession.id==AttendanceRecord.session_id).where(AttendanceRecord.tenant_id==user.tenant_id,AttendanceRecord.student_id.in_(linked),AttendanceSession.tenant_id==user.tenant_id,AttendanceSession.status=="SUBMITTED")) or 0
            attendance_present=db.scalar(select(func.count()).select_from(AttendanceRecord).join(AttendanceSession,AttendanceSession.id==AttendanceRecord.session_id).where(AttendanceRecord.tenant_id==user.tenant_id,AttendanceRecord.student_id.in_(linked),AttendanceRecord.status=="PRESENT",AttendanceSession.tenant_id==user.tenant_id,AttendanceSession.status=="SUBMITTED")) or 0
        attendance_rate="—" if not attendance_total else f"{round((attendance_present/attendance_total)*100)}%"
        visible_notice_count=count(db,Notice,user.tenant_id,Notice.status=="PUBLISHED",Notice.audience.in_({"ALL","PARENT"}))
        metrics=[
            {"label":"Linked children","value":student_count,"href":"/students"},
            {"label":"Open invoices","value":invoice_count,"href":"/finance"},
            {"label":"Attendance","value":attendance_rate,"href":"/attendance"},
            {"label":"Published notices","value":visible_notice_count,"href":"/communication"},
        ]
        heading="Your family overview"; description="A summary of your linked students and current academy activity."
    elif "TEACHER" in roles:
        sections=teacher_section_ids(db,user)
        attendance_count=0 if not sections else count(db,AttendanceSession,user.tenant_id,AttendanceSession.section_id.in_(sections))
        metrics=[
            {"label":"Assigned sections","value":len(sections),"href":"/learning"},
            {"label":"Attendance sessions","value":attendance_count,"href":"/attendance"},
            {"label":"Learning workspace","value":"Courses & assessments","href":"/learning"},
            {"label":"Role","value":"TEACHER","href":None},
        ]
        heading="Your teaching workspace"; description="Assigned classes, attendance and learning activity."
    elif "ACCOUNTS" in roles:
        metrics=[
            {"label":"Open invoices","value":count(db,Invoice,user.tenant_id,Invoice.status!="PAID"),"href":"/finance"},
            {"label":"Finance workspace","value":"Billing & payments","href":"/finance"},
            {"label":"Role","value":"ACCOUNTS","href":None},
        ]
        heading="Finance workspace"; description="Fee, invoice and payment operations for your institution."
    elif "HR" in roles:
        metrics=[
            {"label":"Active staff","value":count(db,Staff,user.tenant_id,Staff.status=="ACTIVE"),"href":"/staff"},
            {"label":"Role","value":"HR / STAFF","href":None},
        ]
        heading="People workspace"; description="Staff and workforce administration."
    elif "CAMPUS_ADMIN" in roles:
        metrics=[
            {"label":"Campus operations","value":"Active","href":"/campus"},
            {"label":"Integrations","value":"Manage","href":"/campus"},
            {"label":"Role","value":"CAMPUS ADMIN","href":None},
        ]
        heading="Campus operations workspace"; description="Operational services, integrations, grievances and assets."
    elif "AUDITOR" in roles:
        metrics=[
            {"label":"Audit mode","value":"READ ONLY","href":"/reports"},
            {"label":"Role","value":"AUDITOR","href":None},
        ]
        heading="Audit workspace"; description="Read-only institutional reporting and audit visibility."
    else:
        metrics=[
            {"label":"Active students","value":count(db,Student,user.tenant_id,Student.status=="ACTIVE"),"href":"/students"},
            {"label":"Active staff","value":count(db,Staff,user.tenant_id,Staff.status=="ACTIVE"),"href":"/staff"},
            {"label":"Attendance sessions","value":count(db,AttendanceSession,user.tenant_id),"href":"/attendance"},
            {"label":"Open invoices","value":count(db,Invoice,user.tenant_id,Invoice.status!="PAID"),"href":"/finance"},
        ]
        heading="Academy overview"; description="Current operational indicators for your institution."
    return {"data":{"tenant_id":str(user.tenant_id),"email":user.email,"platform":"ONLINE","tenant_isolation":"ENABLED","rbac":"ENABLED" if permissions else "NO_PERMISSIONS","audit":"ENABLED","heading":heading,"description":description,"metrics":metrics},"request_id":request.state.request_id}

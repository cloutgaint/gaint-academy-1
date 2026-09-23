from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.identity import Tenant, Campus, User, Role, Permission, UserRole, RolePermission
STUDENT_PERMISSIONS=["platform.dashboard.view","students.student.view","timetable.slot.view","attendance.session.view","learning.course.view","learning.submission.create","communication.notice.view","finance.plan.view","finance.payment.initiate","reports.summary.view"]
TEACHER_PERMISSIONS=["platform.dashboard.view","students.student.view","timetable.slot.view","attendance.session.create","attendance.record.mark","attendance.session.submit","learning.course.view","learning.course.manage","learning.assignment.manage","assessment.manage","assessment.marks.manage","assessment.publish","communication.notice.view","reports.summary.view"]
PARENT_PERMISSIONS=["platform.dashboard.view","students.student.view","attendance.session.view","learning.course.view","communication.notice.view","finance.plan.view","finance.payment.initiate","reports.summary.view"]
ACCOUNTS_PERMISSIONS=["platform.dashboard.view","finance.plan.view","finance.plan.manage","finance.invoice.create","finance.payment.record","communication.notice.view"]
HR_PERMISSIONS=["platform.dashboard.view","staff.staff.view","staff.staff.create","communication.notice.view"]
CAMPUS_ADMIN_PERMISSIONS=["platform.dashboard.view","integrations.view","integrations.manage","grievances.manage","assets.manage","communication.notice.view"]
AUDITOR_PERMISSIONS=["platform.dashboard.view","reports.summary.view","audit.event.view","communication.notice.view"]
PERMISSIONS=["platform.dashboard.view","users.user.view","users.user.create","students.student.view","students.student.create","staff.staff.view","staff.staff.create","timetable.slot.manage","timetable.slot.view","attendance.session.create","attendance.record.mark","attendance.session.submit","learning.course.manage","learning.course.view","learning.submission.create","learning.assignment.manage","assessment.manage","assessment.marks.manage","assessment.publish","finance.plan.view","finance.plan.manage","finance.invoice.create","finance.payment.record","finance.payment.initiate","communication.notice.manage","communication.notice.view","communication.notice.publish","reports.summary.view","integrations.view","integrations.manage","grievances.manage","assets.manage","ai.use","ai.action.propose","ai.action.confirm","academics.setup.admin","audit.event.view"]
def run():
    if not settings.seed_admin_password: raise RuntimeError("SEED_ADMIN_PASSWORD must be set.")
    with SessionLocal() as db:
        tenant=db.scalar(select(Tenant).where(Tenant.code=="GAINT"))
        if not tenant:
            tenant=Tenant(name="GAINT Academy Development",code="GAINT"); db.add(tenant); db.flush()
            db.add(Campus(tenant_id=tenant.id,name="Main Campus",code="MAIN"))
        role=db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.code=="INSTITUTION_ADMIN"))
        if not role:
            role=Role(tenant_id=tenant.id,code="INSTITUTION_ADMIN",name="Institution Admin"); db.add(role); db.flush()
        for code in PERMISSIONS:
            p=db.scalar(select(Permission).where(Permission.code==code))
            if not p: p=Permission(code=code); db.add(p); db.flush()
            if not db.scalar(select(RolePermission).where(RolePermission.role_id==role.id,RolePermission.permission_id==p.id)):
                db.add(RolePermission(role_id=role.id,permission_id=p.id))
        student_role=db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.code=="STUDENT"))
        if not student_role:
            student_role=Role(tenant_id=tenant.id,code="STUDENT",name="Student"); db.add(student_role); db.flush()
        for code in STUDENT_PERMISSIONS:
            p=db.scalar(select(Permission).where(Permission.code==code))
            if not p: p=Permission(code=code); db.add(p); db.flush()
            if not db.scalar(select(RolePermission).where(RolePermission.role_id==student_role.id,RolePermission.permission_id==p.id)):
                db.add(RolePermission(role_id=student_role.id,permission_id=p.id))
        teacher_role=db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.code=="TEACHER"))
        if not teacher_role:
            teacher_role=Role(tenant_id=tenant.id,code="TEACHER",name="Teacher"); db.add(teacher_role); db.flush()
        for code in TEACHER_PERMISSIONS:
            p=db.scalar(select(Permission).where(Permission.code==code))
            if not p: p=Permission(code=code); db.add(p); db.flush()
            if not db.scalar(select(RolePermission).where(RolePermission.role_id==teacher_role.id,RolePermission.permission_id==p.id)):
                db.add(RolePermission(role_id=teacher_role.id,permission_id=p.id))
        parent_role=db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.code=="PARENT"))
        if not parent_role:
            parent_role=Role(tenant_id=tenant.id,code="PARENT",name="Parent"); db.add(parent_role); db.flush()
        for code in PARENT_PERMISSIONS:
            p=db.scalar(select(Permission).where(Permission.code==code))
            if not p: p=Permission(code=code); db.add(p); db.flush()
            if not db.scalar(select(RolePermission).where(RolePermission.role_id==parent_role.id,RolePermission.permission_id==p.id)):
                db.add(RolePermission(role_id=parent_role.id,permission_id=p.id))
        operational_roles={
            "ACCOUNTS":("Accounts",ACCOUNTS_PERMISSIONS),
            "HR":("HR / Staff",HR_PERMISSIONS),
            "CAMPUS_ADMIN":("Campus Admin",CAMPUS_ADMIN_PERMISSIONS),
            "AUDITOR":("Auditor",AUDITOR_PERMISSIONS),
        }
        for role_code,(role_name,codes) in operational_roles.items():
            op_role=db.scalar(select(Role).where(Role.tenant_id==tenant.id,Role.code==role_code))
            if not op_role:
                op_role=Role(tenant_id=tenant.id,code=role_code,name=role_name);db.add(op_role);db.flush()
            for code in codes:
                p=db.scalar(select(Permission).where(Permission.code==code))
                if not p:p=Permission(code=code);db.add(p);db.flush()
                if not db.scalar(select(RolePermission).where(RolePermission.role_id==op_role.id,RolePermission.permission_id==p.id)):
                    db.add(RolePermission(role_id=op_role.id,permission_id=p.id))
        user=db.scalar(select(User).where(User.tenant_id==tenant.id,User.email==settings.seed_admin_email))
        if not user:
            user=User(tenant_id=tenant.id,email=settings.seed_admin_email,password_hash=hash_password(settings.seed_admin_password)); db.add(user); db.flush()
        if not db.scalar(select(UserRole).where(UserRole.tenant_id==tenant.id,UserRole.user_id==user.id,UserRole.role_id==role.id)):
            db.add(UserRole(tenant_id=tenant.id,user_id=user.id,role_id=role.id))
        db.commit(); print("Seeded admin:",settings.seed_admin_email)
if __name__=="__main__": run()

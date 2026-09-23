from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_teacher_account_requires_user_creation_permission():
 s=read("app/api/v1/people.py")
 block=s[s.index('class TeacherAccountIn'):]
 assert 'require(db,user,"users.user.create")' in block

def test_teacher_account_is_tenant_and_active_staff_scoped():
 s=read("app/api/v1/people.py")
 block=s[s.index('class TeacherAccountIn'):]
 assert "Staff.tenant_id==user.tenant_id" in block
 assert 'Staff.status=="ACTIVE"' in block

def test_teacher_identity_is_staff_resource_scoped():
 s=read("app/api/v1/people.py")
 block=s[s.index('class TeacherAccountIn'):]
 assert 'Role.code=="TEACHER"' in block
 assert 'scope_type="STAFF"' in block
 assert 'scope_id=str(staff.id)' in block

def test_duplicate_staff_binding_and_email_are_rejected():
 s=read("app/api/v1/people.py")
 block=s[s.index('class TeacherAccountIn'):]
 assert '"Staff already has a teacher account"' in block
 assert '"Email already exists"' in block

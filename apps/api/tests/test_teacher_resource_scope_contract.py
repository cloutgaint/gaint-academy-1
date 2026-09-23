from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_teacher_scope_uses_staff_assignment_and_tenant():
    s=read("app/core/auth.py")
    assert 'scope["role"]=="TEACHER"' in s
    assert 'scope["scope_type"]=="STAFF"' in s
    assert "TeacherAssignment.tenant_id==user.tenant_id" in s
    assert "TeacherAssignment.staff_id==staff_id" in s

def test_attendance_mutations_require_teacher_section():
    s=read("app/api/v1/attendance.py")
    assert "require_teacher_section(db,u,p.section_id)" in s
    assert s.count("require_teacher_section(db,u,s.section_id)") >= 2
    assert "require_teacher_section(db,u,section_id)" in s

def test_learning_teacher_visibility_and_mutations_are_scoped():
    s=read("app/api/v1/learning.py")
    assert 'has_role(db,u,"TEACHER")' in s
    assert "Course.section_id.in_(sections)" in s
    assert s.count("require_teacher_section(db,u,c.section_id)") >= 2
    assert s.count("require_teacher_section(db,u,course.section_id)") >= 2

def test_teacher_permissions_seeded():
    s=read("app/scripts/seed.py")
    line=next(x for x in s.splitlines() if x.startswith("TEACHER_PERMISSIONS="))
    for permission in ["attendance.session.create","attendance.record.mark","learning.course.view","assessment.marks.manage"]:
        assert f'"{permission}"' in line

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_academics_api_lists_classes_and_sections_by_tenant():
 s=read("app/api/v1/academics.py")
 assert '@router.get("/classes")' in s
 assert 'AcademicClass.tenant_id==user.tenant_id' in s
 assert 'AcademicClass.academic_year_id==academic_year_id' in s
 assert '@router.get("/sections")' in s
 assert 'Section.tenant_id==user.tenant_id' in s
 assert 'Section.class_id==class_id' in s

def test_academics_ui_supports_year_class_section_flow():
 s=(ROOT.parent/"web/app/academics/page.tsx").read_text(encoding="utf-8")
 for phrase in ["Create class","Create section","/academics/classes?academic_year_id=","/academics/sections?class_id=","Next: student enrollment"]:
  assert phrase in s

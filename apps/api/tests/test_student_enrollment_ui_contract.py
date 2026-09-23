from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read_web(p):return (ROOT.parent/"web"/p).read_text(encoding="utf-8")

def test_student360_has_cascading_enrollment_ui():
 s=read_web("app/students/[id]/page.tsx")
 for phrase in [
  "Enroll student",
  "/academics/classes?academic_year_id=",
  "/academics/sections?class_id=",
  'apiFetch("/students/"+id+"/enroll"',
  "Student enrolled successfully."
 ]:
  assert phrase in s

def test_enrollment_form_hidden_after_active_enrollment():
 s=read_web("app/students/[id]/page.tsx")
 assert "!s.enrollment&&<section" in s

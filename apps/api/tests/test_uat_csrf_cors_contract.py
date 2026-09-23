from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_cors_allows_csrf_header():
 s=read("app/core/cors.py")
 assert '"X-CSRF-Token"' in s
 assert 'allow_credentials=True' in s

def test_academics_page_surfaces_api_errors():
 s=(ROOT.parent/"web/app/academics/page.tsx").read_text(encoding="utf-8")
 assert "isAuthError" in s
 assert "Unable to create academic year" in s
 assert 'className="error"' in s

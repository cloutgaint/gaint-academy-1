from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_csrf_middleware_protects_cookie_authenticated_mutations():
 s=read("app/core/csrf.py")
 assert 'SAFE_METHODS={"GET","HEAD","OPTIONS"}' in s
 assert "request.cookies.get(SESSION_COOKIE)" in s
 assert "request.headers.get(CSRF_HEADER)" in s
 assert "secrets.compare_digest(cookie,header)" in s
 assert 'status_code=403' in s

def test_login_issues_csrf_cookie_and_logout_clears_it():
 s=read("app/api/v1/auth.py")
 login=s[s.index('@router.post("/login")'):s.index('@router.post("/forgot-password")')]
 assert "new_csrf_token()" in login
 assert "response.set_cookie(CSRF_COOKIE" in login
 logout=s[s.index('@router.post("/logout")'):]
 assert "response.delete_cookie(CSRF_COOKIE" in logout

def test_authenticated_session_can_bootstrap_csrf_token():
 s=read("app/api/v1/auth.py")
 block=s[s.index('@router.get("/csrf")'):s.index('@router.post("/logout")')]
 assert "user:User=Depends(current_user)" in block
 assert '"csrf_token":token' in block

def test_web_client_attaches_csrf_to_authenticated_mutations():
 s=read("../web/lib/api.ts")
 assert 'headers["X-CSRF-Token"]=await ensureCsrf()' in s
 assert 'PUBLIC_MUTATIONS' in s
 assert '"/auth/login"' in s

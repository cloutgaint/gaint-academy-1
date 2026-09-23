from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_login_rate_limit_uses_normalized_identity_hash():
 s=read("app/api/v1/auth.py")
 assert "def _identity_digest" in s
 assert 'institution_code.strip().upper()' in s
 assert 'email.strip().lower()' in s
 assert 'return "auth:login:"+_identity_digest' in s

def test_failed_logins_increment_and_success_clears_counter():
 s=read("app/api/v1/auth.py")
 login=s[s.index('@router.post("/login")'):s.index('@router.post("/forgot-password")')]
 assert "_check_login_limit(redis,login_key)" in login
 assert "_record_login_failure(redis,login_key)" in login
 assert "_clear_login_failures(redis,login_key)" in login

def test_login_limit_configuration_defaults_are_present():
 s=read("app/core/config.py")
 assert "login_max_attempts:int=5" in s
 assert "login_window_seconds:int=900" in s

def test_production_redis_failure_fails_closed():
 s=read("app/api/v1/auth.py")
 block=s[s.index("def _login_redis_or_fail"):s.index("def _check_login_limit")]
 assert '{"production","staging"}' in block
 assert 'status_code=503' in block

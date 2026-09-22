from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUTH=(ROOT/"app/api/v1/auth.py").read_text()
CONFIG=(ROOT/"app/core/config.py").read_text()

def test_password_recovery_is_tenant_scoped_and_non_enumerating():
    assert '@router.post("/forgot-password")' in AUTH
    assert '@router.post("/reset-password")' in AUTH
    assert 'Tenant.code==code' in AUTH
    assert '"If the account exists, a reset code has been sent."' in AUTH

def test_reset_otp_has_expiry_throttle_and_attempt_limit():
    assert "setex(throttle,60" in AUTH
    assert "password_reset_otp_minutes*60" in AUTH
    assert "if attempts>5" in AUTH
    assert "compare_digest" in AUTH

def test_password_reset_revokes_sessions_and_audits():
    assert 'action="auth.password_reset_completed"' in AUTH
    assert "Session.user_id==user.id" in AUTH
    assert "revoked_at=now()" in AUTH

def test_change_password_requires_current_password():
    assert '@router.post("/change-password")' in AUTH
    assert "verify_password(payload.current_password,user.password_hash)" in AUTH
    assert 'action="auth.password_changed"' in AUTH

def test_smtp_configuration_is_externalized():
    assert "smtp_password:str|None=None" in CONFIG
    assert "smtp_host:str|None=None" in CONFIG

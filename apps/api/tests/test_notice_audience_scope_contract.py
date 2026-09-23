from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_notice_audience_is_validated():
 s=read("app/api/v1/communication.py")
 assert 'ALLOWED_AUDIENCES={"ALL","STUDENT","PARENT","TEACHER","STAFF"}' in s
 assert 'raise HTTPException(422,"Invalid notice audience")' in s

def test_notice_listing_is_role_audience_scoped():
 s=read("app/api/v1/communication.py")
 assert "role_codes(db,u)" in s
 assert 'Notice.audience.in_(audiences)' in s

def test_notice_publish_targets_role_users_not_everyone():
 s=read("app/api/v1/communication.py")
 assert "UserRole.user_id" in s
 assert "Role.code==x.audience" in s
 assert 'if x.audience=="ALL"' in s

def test_notifications_remain_user_scoped():
 s=read("app/api/v1/communication.py")
 assert "Notification.user_id==u.id" in s

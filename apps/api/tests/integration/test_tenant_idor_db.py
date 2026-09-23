import os
import pytest

pytestmark=pytest.mark.skipif(os.getenv("RUN_DB_INTEGRATION")!="1",reason="requires PostgreSQL integration database")

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.auth import SESSION_COOKIE, new_session_token
from app.db.session import SessionLocal
from app.models.identity import Tenant, User, Role, Permission, RolePermission, UserRole, Session, now
from app.models.academics import Student
from app.models.people import Guardian, StudentGuardian

client=TestClient(app)

def _permission(db,code):
    p=db.scalar(select(Permission).where(Permission.code==code))
    if not p:
        p=Permission(code=code);db.add(p);db.flush()
    return p

def _tenant_user(db,label,role_code="INSTITUTION_ADMIN",scope_type="TENANT",scope_id=None):
    suffix=uuid.uuid4().hex[:10]
    tenant=Tenant(name=f"{label} Tenant",code=f"{label[:4].upper()}{suffix}",status="ACTIVE")
    db.add(tenant);db.flush()
    user=User(tenant_id=tenant.id,email=f"{label.lower()}-{suffix}@example.test",password_hash="not-used",is_active=True)
    db.add(user);db.flush()
    role=Role(tenant_id=tenant.id,code=role_code,name=role_code)
    db.add(role);db.flush()
    permission=_permission(db,"students.student.view")
    db.add(RolePermission(role_id=role.id,permission_id=permission.id))
    db.add(UserRole(tenant_id=tenant.id,user_id=user.id,role_id=role.id,scope_type=scope_type,scope_id=scope_id))
    db.flush()
    raw,digest=new_session_token()
    db.add(Session(tenant_id=tenant.id,user_id=user.id,token_hash=digest,expires_at=now()+timedelta(hours=1)))
    db.commit()
    return tenant,user,raw

def test_cross_tenant_student_idor_returns_404():
    with SessionLocal() as db:
        tenant_a,user_a,token=_tenant_user(db,"idorA")
        tenant_b=Tenant(name="IDOR B",code=f"B{uuid.uuid4().hex[:10]}",status="ACTIVE")
        db.add(tenant_b);db.flush()
        foreign=Student(tenant_id=tenant_b.id,admission_no=f"B-{uuid.uuid4().hex[:8]}",first_name="Foreign",status="ACTIVE")
        db.add(foreign);db.commit();foreign_id=foreign.id

    response=client.get(f"/api/v1/students/{foreign_id}",cookies={SESSION_COOKIE:token})
    assert response.status_code==404
    assert response.json()["detail"]=="Student not found"

def test_parent_cannot_idor_unlinked_same_tenant_student():
    with SessionLocal() as db:
        suffix=uuid.uuid4().hex[:10]
        tenant=Tenant(name="Parent Scope",code=f"P{suffix}",status="ACTIVE");db.add(tenant);db.flush()
        linked=Student(tenant_id=tenant.id,admission_no=f"L-{suffix}",first_name="Linked",status="ACTIVE")
        other=Student(tenant_id=tenant.id,admission_no=f"U-{suffix}",first_name="Unlinked",status="ACTIVE")
        db.add_all([linked,other]);db.flush()
        user=User(tenant_id=tenant.id,email=f"parent-{suffix}@example.test",password_hash="not-used",is_active=True)
        db.add(user);db.flush()
        role=Role(tenant_id=tenant.id,code="PARENT",name="Parent");db.add(role);db.flush()
        permission=_permission(db,"students.student.view")
        db.add(RolePermission(role_id=role.id,permission_id=permission.id))
        guardian=Guardian(tenant_id=tenant.id,name="Parent",phone=f"9{uuid.uuid4().int%10**9:09d}",user_id=user.id)
        db.add(guardian);db.flush()
        db.add(StudentGuardian(tenant_id=tenant.id,student_id=linked.id,guardian_id=guardian.id,relationship="PARENT",is_primary=True))
        db.add(UserRole(tenant_id=tenant.id,user_id=user.id,role_id=role.id,scope_type="GUARDIAN",scope_id=str(guardian.id)))
        raw,digest=new_session_token()
        db.add(Session(tenant_id=tenant.id,user_id=user.id,token_hash=digest,expires_at=now()+timedelta(hours=1)))
        db.commit();linked_id=linked.id;other_id=other.id

    linked_response=client.get(f"/api/v1/students/{linked_id}",cookies={SESSION_COOKIE:raw})
    other_response=client.get(f"/api/v1/students/{other_id}",cookies={SESSION_COOKIE:raw})
    assert linked_response.status_code==200
    assert other_response.status_code==404

def test_tenant_student_list_does_not_leak_foreign_rows():
    with SessionLocal() as db:
        tenant_a,user_a,token=_tenant_user(db,"listA")
        own=Student(tenant_id=tenant_a.id,admission_no=f"A-{uuid.uuid4().hex[:8]}",first_name="Own",status="ACTIVE")
        tenant_b=Tenant(name="List B",code=f"LB{uuid.uuid4().hex[:8]}",status="ACTIVE")
        db.add(tenant_b);db.flush()
        foreign=Student(tenant_id=tenant_b.id,admission_no=f"B-{uuid.uuid4().hex[:8]}",first_name="Foreign",status="ACTIVE")
        db.add_all([own,foreign]);db.commit();own_id=str(own.id);foreign_id=str(foreign.id)

    response=client.get("/api/v1/students",cookies={SESSION_COOKIE:token})
    assert response.status_code==200
    ids={row["id"] for row in response.json()["data"]}
    assert own_id in ids
    assert foreign_id not in ids

from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_v11_release_candidate_docs_exist_and_are_linked():
    readme=read("README.md")
    assert "docs/UAT_CHECKLIST.md" in readme
    assert "docs/RELEASE_NOTES_v1.1_RC.md" in readme

def test_uat_gate_covers_security_and_resource_scope():
    uat=read("docs/UAT_CHECKLIST.md")
    for phrase in [
        "CSRF",
        "Cross-tenant student IDs return 404",
        "Teacher can act only on assigned sections",
        "Payment webhook lookup is bound to tenant_id + provider + provider_order_id",
        "zero open P0 defects",
    ]:
        assert phrase in uat

def test_release_notes_do_not_claim_production_readiness():
    notes=read("docs/RELEASE_NOTES_v1.1_RC.md")
    assert "does not authorize production deployment" in notes
    assert "Local Windows validation → UAT/staging" in notes

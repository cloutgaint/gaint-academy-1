from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(path): return (ROOT/path).read_text(encoding="utf-8")

def test_dashboard_summary_is_role_aware_and_tenant_scoped():
    src=text("app/api/v1/dashboard.py")
    assert 'parent="PARENT" in roles' in src
    assert "model.tenant_id==tenant_id" in src
    assert "Guardian.user_id==user.id" in src
    assert '"metrics":metrics' in src

def test_parent_metrics_only_use_linked_students_for_invoices():
    src=text("app/api/v1/dashboard.py")
    assert "Invoice.student_id.in_(linked)" in src
    assert 'StudentGuardian.tenant_id==user.tenant_id' in src

def test_dashboard_ui_does_not_render_duplicate_module_cards():
    src=(ROOT.parent/"web/app/dashboard/DashboardClient.tsx").read_text(encoding="utf-8")
    assert 'className="module-grid"' not in src
    assert 'className="dashboard-kpis"' in src
    assert 'visible.map(m=><a href={m.href}' in src

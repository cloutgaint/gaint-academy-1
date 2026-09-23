from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return (ROOT/p).read_text(encoding="utf-8")

def test_api_client_preserves_http_status():
 s=read("web/lib/api.ts")
 assert "export class ApiError" in s
 assert "status:number" in s
 assert "new ApiError(response.status" in s
 assert "export function isAuthError" in s

def test_dashboard_only_redirects_authentication_failures():
 s=read("web/app/dashboard/DashboardClient.tsx")
 assert "isAuthError(e)" in s
 assert 'router.replace("/login")' in s
 assert "Unable to load workspace" in s

def test_core_module_pages_do_not_treat_every_error_as_logout():
 for path in ["web/app/students/page.tsx","web/app/finance/page.tsx","web/app/settings/page.tsx"]:
  s=read(path)
  assert "isAuthError(e)" in s

def test_global_error_and_not_found_states_exist():
 assert (ROOT/"web/app/error.tsx").exists()
 assert (ROOT/"web/app/not-found.tsx").exists()

def test_settings_security_copy_reflects_csrf_completion():
 s=read("web/app/settings/page.tsx")
 assert "Cookie-authenticated mutations use CSRF protection." in s
 assert "CSRF hardening and advanced resource scopes remain" not in s

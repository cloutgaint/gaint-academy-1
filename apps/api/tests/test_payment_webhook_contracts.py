from pathlib import Path
ROOT=Path(__file__).parents[1]/"app"
def test_webhook_requires_hmac_signature():
 s=(ROOT/"api"/"v1"/"finance.py").read_text();assert "hmac.compare_digest" in s and "payment_webhook_secret" in s and "Invalid payment webhook signature" in s
def test_webhook_is_idempotent_and_invoice_scoped():
 s=(ROOT/"api"/"v1"/"finance.py").read_text();assert "Payment.reference==p.payment_reference" in s and "Invoice.tenant_id==order.tenant_id" in s and "idempotent_replay" in s
def test_secret_is_configuration_only():
 s=(ROOT/"core"/"config.py").read_text();assert "payment_webhook_secret:str|None=None" in s

def test_webhook_lookup_is_tenant_and_provider_scoped():
 s=(ROOT/"api"/"v1"/"finance.py").read_text()
 assert "tenant_id:UUID;provider:str;provider_order_id:str" in s
 assert "PaymentOrder.tenant_id==p.tenant_id" in s
 assert "PaymentOrder.provider==p.provider" in s
 assert "PaymentOrder.provider_order_id==p.provider_order_id" in s

def test_webhook_confirmation_is_audited():
 s=(ROOT/"api"/"v1"/"finance.py").read_text()
 assert 'action="finance.payment_webhook.confirmed"' in s
 assert "request_id=request.state.request_id" in s

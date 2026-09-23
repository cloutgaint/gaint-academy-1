from decimal import Decimal
import hashlib,hmac
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Header,Request
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user,permission_codes,has_role,linked_student_ids,require_linked_student
from app.core.config import settings
from app.db.session import get_db
from app.models.identity import User,AuditEvent
from app.models.academics import Student
from app.models.finance import FeePlan,Invoice,Payment,PaymentOrder
router=APIRouter(prefix="/finance",tags=["finance"])
def req(db,u,p):
 if p not in permission_codes(db,u):raise HTTPException(403,"Permission denied")
class FeePlanIn(BaseModel):name:str;amount:Decimal=Field(gt=0)
@router.post("/fee-plans",status_code=201)
def plan(p:FeePlanIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"finance.plan.manage");x=FeePlan(tenant_id=u.tenant_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"name":x.name,"amount":str(x.amount)}}
@router.get("/fee-plans")
def plans(u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"finance.plan.view")
 if has_role(db,u,"PARENT"):
  ids=linked_student_ids(db,u)
  rows=db.scalars(select(Invoice).where(Invoice.tenant_id==u.tenant_id,Invoice.student_id.in_(ids))).all() if ids else []
  return {"data":[{"id":str(x.id),"invoice_no":x.invoice_no,"amount":str(x.amount),"paid_amount":str(x.paid_amount),"status":x.status,"student_id":str(x.student_id)} for x in rows]}
 rows=db.scalars(select(FeePlan).where(FeePlan.tenant_id==u.tenant_id)).all();return {"data":[{"id":str(x.id),"name":x.name,"amount":str(x.amount),"status":x.status} for x in rows]}
class InvoiceIn(BaseModel):student_id:UUID;fee_plan_id:UUID;invoice_no:str
@router.post("/invoices",status_code=201)
def invoice(p:InvoiceIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"finance.invoice.create");student=db.scalar(select(Student).where(Student.id==p.student_id,Student.tenant_id==u.tenant_id));plan=db.scalar(select(FeePlan).where(FeePlan.id==p.fee_plan_id,FeePlan.tenant_id==u.tenant_id,FeePlan.status=="ACTIVE"))
 if not student or not plan:raise HTTPException(404,"Invoice resource not found")
 x=Invoice(tenant_id=u.tenant_id,student_id=student.id,fee_plan_id=plan.id,invoice_no=p.invoice_no,amount=plan.amount);db.add(x);db.commit();db.refresh(x);return {"data":{"id":str(x.id),"invoice_no":x.invoice_no,"amount":str(x.amount),"status":x.status}}
class PaymentIn(BaseModel):invoice_id:UUID;reference:str;amount:Decimal=Field(gt=0);method:str
@router.post("/payments",status_code=201)
def payment(p:PaymentIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"finance.payment.record");inv=db.scalar(select(Invoice).where(Invoice.id==p.invoice_id,Invoice.tenant_id==u.tenant_id))
 if inv: require_linked_student(db,u,inv.student_id)
 if not inv:raise HTTPException(404,"Invoice not found")
 due=inv.amount-inv.paid_amount
 if p.amount>due:raise HTTPException(422,"Payment exceeds invoice balance")
 x=Payment(tenant_id=u.tenant_id,**p.model_dump(),status="CONFIRMED");db.add(x);inv.paid_amount+=p.amount;inv.status="PAID" if inv.paid_amount==inv.amount else "PARTIALLY_PAID";db.flush();db.add(AuditEvent(tenant_id=u.tenant_id,user_id=u.id,action="finance.payment.confirmed",resource_type="payment",resource_id=str(x.id)));db.commit();db.refresh(x);return {"data":{"id":str(x.id),"status":x.status,"invoice_status":inv.status,"balance":str(inv.amount-inv.paid_amount)}}

class PaymentOrderIn(BaseModel):
 invoice_id:UUID;provider:str;provider_order_id:str;idempotency_key:str
@router.post("/payment-orders",status_code=201)
def create_payment_order(p:PaymentOrderIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 req(db,u,"finance.payment.record")
 existing=db.scalar(select(PaymentOrder).where(PaymentOrder.tenant_id==u.tenant_id,PaymentOrder.idempotency_key==p.idempotency_key))
 if existing:return {"data":{"id":str(existing.id),"status":existing.status,"provider_order_id":existing.provider_order_id,"idempotent_replay":True}}
 inv=db.scalar(select(Invoice).where(Invoice.id==p.invoice_id,Invoice.tenant_id==u.tenant_id))
 if not inv:raise HTTPException(404,"Invoice not found")
 due=inv.amount-inv.paid_amount
 if due<=0:raise HTTPException(409,"Invoice has no outstanding balance")
 x=PaymentOrder(tenant_id=u.tenant_id,invoice_id=inv.id,provider=p.provider,provider_order_id=p.provider_order_id,idempotency_key=p.idempotency_key,amount=due,status="CREATED")
 db.add(x);db.flush();db.add(AuditEvent(tenant_id=u.tenant_id,user_id=u.id,action="finance.payment_order.created",resource_type="payment_order",resource_id=str(x.id)));db.commit();db.refresh(x)
 return {"data":{"id":str(x.id),"status":x.status,"provider_order_id":x.provider_order_id,"amount":str(x.amount),"idempotent_replay":False}}

class WebhookIn(BaseModel):
 provider_order_id:str;payment_reference:str;status:str
@router.post("/webhooks/payment")
async def payment_webhook(p:WebhookIn,request:Request,x_payment_signature:str|None=Header(default=None),db:Session=Depends(get_db)):
 if not settings.payment_webhook_secret:raise HTTPException(503,"Payment webhook is not configured")
 raw=await request.body();expected=hmac.new(settings.payment_webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
 if not x_payment_signature or not hmac.compare_digest(expected,x_payment_signature):raise HTTPException(401,"Invalid payment webhook signature")
 order=db.scalar(select(PaymentOrder).where(PaymentOrder.provider_order_id==p.provider_order_id))
 if not order:raise HTTPException(404,"Payment order not found")
 if p.status!="CONFIRMED":return {"data":{"id":str(order.id),"status":order.status,"processed":False}}
 existing=db.scalar(select(Payment).where(Payment.tenant_id==order.tenant_id,Payment.reference==p.payment_reference))
 if existing:return {"data":{"id":str(order.id),"status":order.status,"processed":False,"idempotent_replay":True}}
 inv=db.scalar(select(Invoice).where(Invoice.id==order.invoice_id,Invoice.tenant_id==order.tenant_id))
 if not inv:raise HTTPException(404,"Invoice not found")
 due=inv.amount-inv.paid_amount
 amount=min(order.amount,due)
 if amount<=0:raise HTTPException(409,"Invoice has no outstanding balance")
 payment=Payment(tenant_id=order.tenant_id,invoice_id=inv.id,reference=p.payment_reference,amount=amount,method=order.provider,status="CONFIRMED");db.add(payment);inv.paid_amount+=amount;inv.status="PAID" if inv.paid_amount==inv.amount else "PARTIALLY_PAID";order.status="CONFIRMED";db.commit()
 return {"data":{"id":str(order.id),"status":order.status,"processed":True}}

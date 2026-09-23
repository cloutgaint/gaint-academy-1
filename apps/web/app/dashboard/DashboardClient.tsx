"use client";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {apiFetch,isAuthError} from "../../lib/api";
import LogoutButton from "../../components/LogoutButton";
type Me={email:string;permissions:string[];roles:string[]};
type Metric={label:string;value:string|number;href:string|null};
type Summary={platform:string;tenant_isolation:string;rbac:string;audit:string;heading:string;description:string;metrics:Metric[]};
type Module={name:string;href:string;permissions:string[]};
const modules:Module[]=[
 {name:"Academics",href:"/academics",permissions:["academics.setup.admin"]},{name:"Students",href:"/students",permissions:["students.student.view"]},{name:"Staff",href:"/staff",permissions:["staff.staff.view"]},{name:"Attendance",href:"/attendance",permissions:["attendance.session.create","attendance.record.mark","attendance.session.view"]},{name:"Learning",href:"/learning",permissions:["learning.course.view","learning.course.manage"]},{name:"Finance",href:"/finance",permissions:["finance.plan.view","finance.plan.manage","finance.payment.record"]},{name:"Communication",href:"/communication",permissions:["communication.notice.view","communication.notice.manage"]},{name:"Reports",href:"/reports",permissions:["reports.summary.view"]},{name:"Campus Operations",href:"/campus",permissions:["integrations.view","grievances.manage","assets.manage"]},{name:"GAINT AI",href:"/ai",permissions:["ai.use"]},{name:"Settings",href:"/settings",permissions:[]}
];
const adminRoles=new Set(["GAINT_SUPER_ADMIN","INSTITUTION_ADMIN","PRINCIPAL"]);
function roleLabel(roles:string[]){if(roles.some(r=>adminRoles.has(r)))return "INSTITUTION ADMIN";if(roles.includes("PARENT"))return "PARENT / GUARDIAN";if(roles.includes("TEACHER"))return "TEACHER";if(roles.includes("STUDENT"))return "STUDENT";if(roles.includes("ACCOUNTS"))return "ACCOUNTS";if(roles.includes("HR"))return "HR / STAFF";if(roles.includes("AUDITOR"))return "AUDITOR";return roles[0]?.replaceAll("_"," ")||"USER"}
export default function DashboardClient(){
 const router=useRouter();const [me,setMe]=useState<Me|null>(null);const [s,setS]=useState<Summary|null>(null);const [error,setError]=useState("");
 useEffect(()=>{Promise.all([apiFetch("/auth/me"),apiFetch("/dashboard/summary")]).then(([m,d])=>{setMe(m.data);setS(d.data)}).catch(e=>{if(isAuthError(e))router.replace("/login");else setError(e instanceof Error?e.message:"Unable to load dashboard")})},[router]);
 if(error)return <main className="state-page"><section className="state-card"><p className="eyebrow">DASHBOARD</p><h1>Unable to load workspace</h1><p className="error">{error}</p><button onClick={()=>location.reload()}>Try again</button></section></main>;
 if(!me||!s)return <main className="loading">Loading secure workspace…</main>;
 const visible=modules.filter(m=>m.permissions.length===0||m.permissions.some(p=>me.permissions.includes(p)));const parent=me.roles.includes("PARENT");const student=me.roles.includes("STUDENT");const teacher=me.roles.includes("TEACHER");
 return <main className="dashboard-shell"><aside><div className="logo">GA</div><strong>GAINT Academy</strong><nav><a className="active" href="/dashboard">Dashboard</a>{visible.map(m=><a href={m.href} key={m.href}>{m.name}</a>)}</nav></aside>
 <section className="workspace"><header><div><p className="eyebrow">{roleLabel(me.roles)}</p><h1>{parent?"Parent Dashboard":student?"Student Dashboard":teacher?"Teacher Dashboard":"Dashboard"}</h1><p className="muted">{me.email}</p></div><div className="header-actions"><span className="status-pill">v1.1</span><LogoutButton/></div></header>
 <div className="welcome"><h2>{s.heading}</h2><p>{s.description}</p></div>
 <section className="dashboard-kpis">{s.metrics.map(x=>{const body=<><span>{x.label}</span><strong>{x.value}</strong>{x.href&&<small>View details →</small>}</>;return x.href?<a className="kpi-card" href={x.href} key={x.label}>{body}</a>:<article className="kpi-card" key={x.label}>{body}</article>})}</section>
 <section className="dashboard-section"><div><p className="eyebrow">WORKSPACE STATUS</p><h2>Security & platform</h2></div><div className="status-row"><span>Platform <b>{s.platform}</b></span><span>Tenant isolation <b>{s.tenant_isolation}</b></span><span>RBAC <b>{s.rbac}</b></span><span>Audit <b>{s.audit}</b></span></div></section>
 </section></main>
}
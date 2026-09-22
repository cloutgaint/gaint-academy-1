"use client";
import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../lib/api";
import LogoutButton from "../../components/LogoutButton";
type Me={email:string;permissions:string[];roles:string[];scopes:{role:string;scope_type:string;scope_id:string|null}[]};
type Summary={platform:string;tenant_isolation:string;rbac:string;audit:string};
type Module={name:string;href:string;desc:string;permissions:string[];roles?:string[]};
const modules:Module[]=[
 {name:"Academics",href:"/academics",desc:"Academic years, classes and sections",permissions:["academics.setup.admin"]},
 {name:"Students",href:"/students",desc:"Student profiles, guardians and enrolment",permissions:["students.student.view"]},
 {name:"Staff",href:"/staff",desc:"Staff records and teacher assignments",permissions:["staff.staff.view"]},
 {name:"Attendance",href:"/attendance",desc:"Timetable-linked attendance workflows",permissions:["attendance.session.create","attendance.record.mark","attendance.session.view"]},
 {name:"Learning",href:"/learning",desc:"Courses, assignments and assessments",permissions:["learning.course.view","learning.course.manage"]},
 {name:"Finance",href:"/finance",desc:"Fee plans, invoices and payments",permissions:["finance.plan.view","finance.plan.manage","finance.payment.record"]},
 {name:"Communication",href:"/communication",desc:"Notices and notifications",permissions:["communication.notice.view","communication.notice.manage"]},
 {name:"Reports",href:"/reports",desc:"Institution reporting and summaries",permissions:["reports.summary.view"]},
 {name:"Campus Operations",href:"/campus",desc:"Grievances, assets and integrations",permissions:["integrations.view","grievances.manage","assets.manage"]},
 {name:"GAINT AI",href:"/ai",desc:"Permission-aware Academy Copilot",permissions:["ai.use"]},
 {name:"Settings",href:"/settings",desc:"Account and security settings",permissions:[]}
];
const adminRoles=new Set(["GAINT_SUPER_ADMIN","INSTITUTION_ADMIN","PRINCIPAL"]);
function roleLabel(roles:string[]){if(roles.some(r=>adminRoles.has(r)))return "INSTITUTION ADMIN";if(roles.includes("PARENT"))return "PARENT / GUARDIAN";if(roles.includes("TEACHER"))return "TEACHER";if(roles.includes("STUDENT"))return "STUDENT";if(roles.includes("ACCOUNTS"))return "ACCOUNTS";if(roles.includes("HR"))return "HR / STAFF";return roles[0]?.replaceAll("_"," ")||"USER"}
export default function DashboardClient(){
 const router=useRouter(); const [me,setMe]=useState<Me|null>(null); const [s,setS]=useState<Summary|null>(null);
 useEffect(()=>{Promise.all([apiFetch("/auth/me"),apiFetch("/dashboard/summary")]).then(([m,d])=>{setMe(m.data);setS(d.data)}).catch(()=>router.replace("/login"));},[router]);
 if(!me||!s) return <main className="loading">Loading secure workspace…</main>;
 const visible=modules.filter(m=>m.permissions.length===0||m.permissions.some(p=>me.permissions.includes(p)));
 const parent=me.roles.includes("PARENT");
 return <main className="dashboard-shell"><aside><div className="logo">GA</div><strong>GAINT Academy</strong><nav>
 <a className="active" href="/dashboard">Dashboard</a>{visible.map(m=><a href={m.href} key={m.href}>{m.name}</a>)}
 </nav></aside>
 <section className="workspace"><header><div><p className="eyebrow">{roleLabel(me.roles)}</p><h1>{parent?"Parent Dashboard":"Dashboard"}</h1><p className="muted">{me.email}</p></div><div className="header-actions"><span className="status-pill">MVP v1.0 RC</span><LogoutButton/></div></header>
 <div className="welcome"><h2>{parent?"Your family workspace":"Academy operations workspace"}</h2><p>{parent?"Access is restricted to students linked to your guardian account.":"Only modules allowed by your effective backend permissions are shown."}</p></div>
 <div className="metric-grid"><article><span>Platform</span><strong>{s.platform}</strong></article><article><span>Tenant isolation</span><strong>{s.tenant_isolation}</strong></article><article><span>RBAC</span><strong>{s.rbac}</strong></article><article><span>Role</span><strong>{roleLabel(me.roles)}</strong></article></div>
 <section className="module-grid">{visible.map(m=><a className="module-card" href={m.href} key={m.href}><strong>{m.name}</strong><span>{m.desc}</span><b>Open →</b></a>)}</section>
 </section></main>;
}

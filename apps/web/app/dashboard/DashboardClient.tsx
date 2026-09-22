"use client";
import { useEffect,useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../lib/api";
import LogoutButton from "../../components/LogoutButton";
type Me={email:string;permissions:string[]};
type Summary={platform:string;tenant_isolation:string;rbac:string;audit:string};
const modules=[
 ["Academics","/academics","Academic years, classes and sections"],
 ["Students","/students","Student profiles, guardians and enrolment"],
 ["Staff","/staff","Staff records and teacher assignments"],
 ["Attendance","/attendance","Timetable-linked attendance workflows"],
 ["Learning","/learning","Courses, assignments and assessments"],
 ["Finance","/finance","Fee plans, invoices and payments"],
 ["Communication","/communication","Notices and notifications"],
 ["Reports","/reports","Institution reporting and summaries"],
 ["Campus Operations","/campus","Grievances, assets and integrations"],
 ["GAINT AI","/ai","Permission-aware Academy Copilot"],
 ["Settings","/settings","Account, RBAC and security overview"]
];
export default function DashboardClient(){
 const router=useRouter(); const [me,setMe]=useState<Me|null>(null); const [s,setS]=useState<Summary|null>(null);
 useEffect(()=>{Promise.all([apiFetch("/auth/me"),apiFetch("/dashboard/summary")]).then(([m,d])=>{setMe(m.data);setS(d.data)}).catch(()=>router.replace("/login"));},[router]);
 if(!me||!s) return <main className="loading">Loading secure workspace…</main>;
 return <main className="dashboard-shell"><aside><div className="logo">GA</div><strong>GAINT Academy</strong><nav>
 <a className="active" href="/dashboard">Dashboard</a><a href="/academics">Academics</a><a href="/students">Students</a><a href="/staff">Staff</a><a href="/attendance">Attendance</a><a href="/learning">Learning</a><a href="/finance">Finance</a><a href="/communication">Communication</a><a href="/reports">Reports</a><a href="/campus">Campus Operations</a><a href="/ai">GAINT AI</a><a href="/settings">Settings</a>
 </nav></aside>
 <section className="workspace"><header><div><p className="eyebrow">INSTITUTION ADMIN</p><h1>Dashboard</h1><p className="muted">{me.email}</p></div><div className="header-actions"><span className="status-pill">MVP v1.0 RC</span><LogoutButton/></div></header>
 <div className="welcome"><h2>Academy operations workspace</h2><p>Tenant-aware administration, academics, learning, finance, communication, campus operations and governed AI are available from one workspace.</p></div>
 <div className="metric-grid"><article><span>Platform</span><strong>{s.platform}</strong></article><article><span>Tenant isolation</span><strong>{s.tenant_isolation}</strong></article><article><span>RBAC</span><strong>{s.rbac}</strong></article><article><span>Audit</span><strong>{s.audit}</strong></article></div>
 <section className="module-grid">{modules.map(([name,href,desc])=><a className="module-card" href={href} key={href}><strong>{name}</strong><span>{desc}</span><b>Open →</b></a>)}</section>
 </section></main>;
}

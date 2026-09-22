"use client";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {apiFetch} from "../../lib/api";
export default function Settings(){
 const router=useRouter();const [me,setMe]=useState<any>(null);
 useEffect(()=>{apiFetch("/auth/me").then(x=>setMe(x.data)).catch(()=>router.replace("/login"))},[router]);
 if(!me)return <main className="loading">Loading settings…</main>;
 return <main className="module-page"><header><div><p className="eyebrow">ADMINISTRATION</p><h1>Settings</h1><p className="muted">Account, tenant security and access configuration overview.</p></div><button className="secondary" onClick={()=>router.push("/dashboard")}>Dashboard</button></header>
 <section className="profile-grid"><article className="panel"><h2>Signed-in account</h2><dl><dt>Email</dt><dd>{me.email}</dd><dt>User ID</dt><dd>{me.user_id}</dd><dt>Tenant ID</dt><dd>{me.tenant_id}</dd></dl></article>
 <article className="panel"><h2>RBAC & Security</h2><p className="muted">Effective backend permissions for this session.</p><div className="permission-list">{me.permissions.map((p:string)=><span className="permission-chip" key={p}>{p}</span>)}</div></article></section>
 <section className="panel settings-note"><h2>Security controls</h2><p>Authorization is enforced by the API. Parent accounts are provisioned from Student 360 and linked to a guardian record. Production MFA, CSRF hardening and advanced resource scopes remain release-hardening items.</p></section>
 </main>;
}
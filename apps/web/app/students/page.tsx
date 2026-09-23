"use client";
import {FormEvent,useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {apiFetch,isAuthError} from "../../lib/api";
type Student={id:string;admission_no:string;name:string;email?:string;status:string};
export default function StudentsPage(){
 const router=useRouter(); const [rows,setRows]=useState<Student[]>([]); const [form,setForm]=useState({admission_no:"",first_name:"",last_name:"",email:""}); const [error,setError]=useState("");
 async function load(){try{setRows((await apiFetch("/students")).data)}catch(e){if(isAuthError(e))router.replace("/login");else setError(e instanceof Error?e.message:"Unable to load students")}}
 useEffect(()=>{load()},[]);
 async function submit(e:FormEvent){e.preventDefault();setError("");try{await apiFetch("/students",{method:"POST",body:JSON.stringify({...form,email:form.email||null})});setForm({admission_no:"",first_name:"",last_name:"",email:""});await load()}catch(e){setError(e instanceof Error?e.message:"Unable to create student")}}
 return <main className="module-page"><header><div><p className="eyebrow">STUDENT MANAGEMENT</p><h1>Students</h1><p className="muted">Tenant-scoped student registry.</p></div><button onClick={()=>router.push("/dashboard")} className="secondary">Dashboard</button></header>
 <section className="two-column"><form className="panel" onSubmit={submit}><h2>Add student</h2><label>Admission No<input value={form.admission_no} onChange={e=>setForm({...form,admission_no:e.target.value})} required/></label><label>First name<input value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})} required/></label><label>Last name<input value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})}/></label><label>Email<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>{error&&<p className="error">{error}</p>}<button>Add student</button></form>
 <section className="panel"><h2>Student registry</h2><div className="student-list">{rows.length?rows.map(s=><button className="student-row" key={s.id} onClick={()=>router.push("/students/"+s.id)}><span><strong>{s.name}</strong><small>{s.admission_no}</small></span><span className="status-pill">{s.status}</span></button>):<p className="muted">No students yet.</p>}</div></section></section></main>;
}

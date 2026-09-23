"use client";
import {FormEvent,useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {apiFetch,isAuthError} from "../../lib/api";
export default function Academics(){
 const router=useRouter();const [years,setYears]=useState<any[]>([]);const [form,setForm]=useState({name:"",start_date:"",end_date:""});const [error,setError]=useState("");
 async function load(){try{setYears((await apiFetch("/academics/years")).data)}catch(e){if(isAuthError(e))router.replace("/login");else setError(e instanceof Error?e.message:"Unable to load academic years")}}
 useEffect(()=>{load()},[]);
 async function submit(e:FormEvent){e.preventDefault();setError("");try{await apiFetch("/academics/years",{method:"POST",body:JSON.stringify(form)});setForm({name:"",start_date:"",end_date:""});await load()}catch(e){setError(e instanceof Error?e.message:"Unable to create academic year")}}
 return <main className="module-page"><header><div><p className="eyebrow">ACADEMIC SETUP</p><h1>Academic Years</h1><p className="muted">Foundation for classes, sections and enrollments.</p></div><button className="secondary" onClick={()=>router.push("/dashboard")}>Dashboard</button></header><section className="two-column"><form className="panel" onSubmit={submit}><h2>Create academic year</h2><label>Name<input placeholder="2026–27" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/></label><label>Start date<input type="date" value={form.start_date} onChange={e=>setForm({...form,start_date:e.target.value})} required/></label><label>End date<input type="date" value={form.end_date} onChange={e=>setForm({...form,end_date:e.target.value})} required/></label>{error&&<p className="error">{error}</p>}<button>Create</button></form><section className="panel"><h2>Academic years</h2>{years.map(y=><div className="simple-row" key={y.id}><strong>{y.name}</strong><span className="status-pill">{y.status}</span></div>)}</section></section></main>;
}

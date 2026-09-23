"use client";
import {FormEvent,useEffect,useState} from "react";
import {useParams,useRouter} from "next/navigation";
import {apiFetch,isAuthError} from "../../../lib/api";

export default function Student360(){
 const {id}=useParams<{id:string}>(); const router=useRouter();
 const [s,setS]=useState<any>(null); const [guardians,setGuardians]=useState<any[]>([]);
 const [years,setYears]=useState<any[]>([]); const [classes,setClasses]=useState<any[]>([]); const [sections,setSections]=useState<any[]>([]);
 const [enroll,setEnroll]=useState({academic_year_id:"",class_id:"",section_id:""});
 const [g,setG]=useState({name:"",phone:"",email:"",relationship:"PARENT"});
 const [account,setAccount]=useState({guardian_id:"",email:"",password:""});
 const [msg,setMsg]=useState(""); const [error,setError]=useState("");

 async function load(){
  try{
   const [student,gs,ys]=await Promise.all([apiFetch("/students/"+id),apiFetch("/students/"+id+"/guardians"),apiFetch("/academics/years")]);
   setS(student.data);setGuardians(gs.data);setYears(ys.data)
  }catch(e){if(isAuthError(e))router.replace("/login");else setError(e instanceof Error?e.message:"Unable to load Student 360")}
 }
 useEffect(()=>{load()},[id]);

 async function chooseYear(yearId:string){
  setEnroll({academic_year_id:yearId,class_id:"",section_id:""});setClasses([]);setSections([]);
  if(!yearId)return;
  try{setClasses((await apiFetch("/academics/classes?academic_year_id="+yearId)).data)}catch(e){setError(e instanceof Error?e.message:"Unable to load classes")}
 }
 async function chooseClass(classId:string){
  setEnroll({...enroll,class_id:classId,section_id:""});setSections([]);
  if(!classId)return;
  try{setSections((await apiFetch("/academics/sections?class_id="+classId)).data)}catch(e){setError(e instanceof Error?e.message:"Unable to load sections")}
 }
 async function submitEnrollment(e:FormEvent){
  e.preventDefault();setError("");setMsg("");
  try{
   await apiFetch("/students/"+id+"/enroll",{method:"POST",body:JSON.stringify(enroll)});
   setMsg("Student enrolled successfully.");await load()
  }catch(e){setError(e instanceof Error?e.message:"Unable to enroll student")}
 }
 async function addGuardian(e:FormEvent){e.preventDefault();setError("");try{await apiFetch("/students/"+id+"/guardians",{method:"POST",body:JSON.stringify({...g,email:g.email||null,is_primary:true})});setG({name:"",phone:"",email:"",relationship:"PARENT"});setMsg("Guardian linked.");await load()}catch(e){setError(e instanceof Error?e.message:"Unable to add guardian")}}
 async function createAccount(e:FormEvent){e.preventDefault();setError("");try{await apiFetch("/guardians/"+account.guardian_id+"/parent-account",{method:"POST",body:JSON.stringify({email:account.email,password:account.password})});setAccount({guardian_id:"",email:"",password:""});setMsg("Parent login created and linked.");await load()}catch(e){setError(e instanceof Error?e.message:"Unable to create parent account")}}

 if(!s)return <main className="loading">Loading Student 360…</main>;
 return <main className="module-page"><header><div><p className="eyebrow">STUDENT 360</p><h1>{s.first_name} {s.last_name||""}</h1><p className="muted">{s.admission_no}</p></div><button className="secondary" onClick={()=>router.push("/students")}>Back</button></header>
 {msg&&<p className="status">{msg}</p>}{error&&<p className="error">{error}</p>}

 <section className="profile-grid">
  <article className="panel"><h2>Profile</h2><dl><dt>Email</dt><dd>{s.email||"—"}</dd><dt>Status</dt><dd>{s.status}</dd></dl></article>
  <article className="panel"><h2>Current enrollment</h2>{s.enrollment?<dl><dt>Academic Year</dt><dd>{s.enrollment.academic_year_id}</dd><dt>Class</dt><dd>{s.enrollment.class_id}</dd><dt>Section</dt><dd>{s.enrollment.section_id}</dd></dl>:<p className="muted">Not enrolled yet.</p>}</article>
 </section>

 {!s.enrollment&&<section className="panel settings-note"><h2>Enroll student</h2><form onSubmit={submitEnrollment}>
  <label>Academic year<select value={enroll.academic_year_id} onChange={e=>chooseYear(e.target.value)} required><option value="">Select academic year</option>{years.map(y=><option key={y.id} value={y.id}>{y.name}</option>)}</select></label>
  <label>Class<select value={enroll.class_id} onChange={e=>chooseClass(e.target.value)} required disabled={!enroll.academic_year_id}><option value="">Select class</option>{classes.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
  <label>Section<select value={enroll.section_id} onChange={e=>setEnroll({...enroll,section_id:e.target.value})} required disabled={!enroll.class_id}><option value="">Select section</option>{sections.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
  <button>Enroll student</button>
 </form></section>}

 <section className="two-column" style={{marginTop:18}}><form className="panel" onSubmit={addGuardian}><h2>Add guardian</h2><label>Name<input value={g.name} onChange={e=>setG({...g,name:e.target.value})} required/></label><label>Phone<input value={g.phone} onChange={e=>setG({...g,phone:e.target.value})} required/></label><label>Email<input type="email" value={g.email} onChange={e=>setG({...g,email:e.target.value})}/></label><label>Relationship<input value={g.relationship} onChange={e=>setG({...g,relationship:e.target.value})} required/></label><button>Link guardian</button></form>
 <section className="panel"><h2>Guardians & parent access</h2>{guardians.length?guardians.map(x=><div className="simple-row" key={x.guardian_id}><span><strong>{x.name}</strong><small>{x.relationship} · {x.phone}</small></span><span className="status-pill">{x.user_id?"LOGIN LINKED":"NO LOGIN"}</span></div>):<p className="muted">No guardians linked.</p>}
 <form onSubmit={createAccount}><h3>Create parent login</h3><label>Guardian<select value={account.guardian_id} onChange={e=>setAccount({...account,guardian_id:e.target.value})} required><option value="">Select guardian</option>{guardians.filter(x=>!x.user_id).map(x=><option key={x.guardian_id} value={x.guardian_id}>{x.name}</option>)}</select></label><label>Login email<input type="email" value={account.email} onChange={e=>setAccount({...account,email:e.target.value})} required/></label><label>Temporary password<input type="password" minLength={10} value={account.password} onChange={e=>setAccount({...account,password:e.target.value})} required/></label><button>Create parent login</button></form></section></section>
 </main>;
}

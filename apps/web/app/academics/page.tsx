"use client";
import {FormEvent,useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {apiFetch,isAuthError} from "../../lib/api";

type Year={id:string;name:string;status:string};
type AcademicClass={id:string;name:string;academic_year_id:string};
type Section={id:string;name:string;class_id:string};

export default function Academics(){
 const router=useRouter();
 const [years,setYears]=useState<Year[]>([]);
 const [classes,setClasses]=useState<AcademicClass[]>([]);
 const [sections,setSections]=useState<Section[]>([]);
 const [yearForm,setYearForm]=useState({name:"",start_date:"",end_date:""});
 const [classForm,setClassForm]=useState({academic_year_id:"",name:""});
 const [sectionForm,setSectionForm]=useState({class_id:"",name:""});
 const [error,setError]=useState("");
 const [message,setMessage]=useState("");

 async function loadYears(){
  try{setYears((await apiFetch("/academics/years")).data)}
  catch(e){if(isAuthError(e))router.replace("/login");else setError(e instanceof Error?e.message:"Unable to load academic years")}
 }
 async function loadClasses(yearId:string){
  setClasses([]);setSections([]);
  if(!yearId)return;
  try{setClasses((await apiFetch("/academics/classes?academic_year_id="+yearId)).data)}
  catch(e){setError(e instanceof Error?e.message:"Unable to load classes")}
 }
 async function loadSections(classId:string){
  setSections([]);
  if(!classId)return;
  try{setSections((await apiFetch("/academics/sections?class_id="+classId)).data)}
  catch(e){setError(e instanceof Error?e.message:"Unable to load sections")}
 }
 useEffect(()=>{loadYears()},[]);

 async function createYear(e:FormEvent){e.preventDefault();setError("");setMessage("");
  try{
   await apiFetch("/academics/years",{method:"POST",body:JSON.stringify(yearForm)});
   setYearForm({name:"",start_date:"",end_date:""});setMessage("Academic year created.");await loadYears()
  }catch(e){setError(e instanceof Error?e.message:"Unable to create academic year")}
 }
 async function createClass(e:FormEvent){e.preventDefault();setError("");setMessage("");
  try{
   await apiFetch("/academics/classes",{method:"POST",body:JSON.stringify(classForm)});
   setMessage("Class created.");setClassForm({...classForm,name:""});await loadClasses(classForm.academic_year_id)
  }catch(e){setError(e instanceof Error?e.message:"Unable to create class")}
 }
 async function createSection(e:FormEvent){e.preventDefault();setError("");setMessage("");
  try{
   await apiFetch("/academics/sections",{method:"POST",body:JSON.stringify(sectionForm)});
   setMessage("Section created.");setSectionForm({...sectionForm,name:""});await loadSections(sectionForm.class_id)
  }catch(e){setError(e instanceof Error?e.message:"Unable to create section")}
 }

 return <main className="module-page">
  <header><div><p className="eyebrow">ACADEMIC SETUP</p><h1>Academic Structure</h1><p className="muted">Create academic years, classes and sections before enrolling students.</p></div><button className="secondary" onClick={()=>router.push("/dashboard")}>Dashboard</button></header>
  {message&&<p className="status">{message}</p>}{error&&<p className="error">{error}</p>}

  <section className="profile-grid">
   <form className="panel" onSubmit={createYear}><h2>1. Academic year</h2>
    <label>Name<input placeholder="2026-27" value={yearForm.name} onChange={e=>setYearForm({...yearForm,name:e.target.value})} required/></label>
    <label>Start date<input type="date" value={yearForm.start_date} onChange={e=>setYearForm({...yearForm,start_date:e.target.value})} required/></label>
    <label>End date<input type="date" value={yearForm.end_date} onChange={e=>setYearForm({...yearForm,end_date:e.target.value})} required/></label>
    <button>Create year</button>
   </form>
   <section className="panel"><h2>Academic years</h2>{years.length?years.map(y=><button type="button" className="simple-row" key={y.id} onClick={()=>{setClassForm({academic_year_id:y.id,name:""});setSectionForm({class_id:"",name:""});loadClasses(y.id)}}><strong>{y.name}</strong><span className="status-pill">{y.status}</span></button>):<p className="muted">No academic years yet.</p>}</section>
  </section>

  <section className="profile-grid" style={{marginTop:18}}>
   <form className="panel" onSubmit={createClass}><h2>2. Class</h2>
    <label>Academic year<select value={classForm.academic_year_id} onChange={e=>{setClassForm({academic_year_id:e.target.value,name:""});setSectionForm({class_id:"",name:""});loadClasses(e.target.value)}} required><option value="">Select academic year</option>{years.map(y=><option key={y.id} value={y.id}>{y.name}</option>)}</select></label>
    <label>Class name<input placeholder="B.Tech CSE" value={classForm.name} onChange={e=>setClassForm({...classForm,name:e.target.value})} required/></label>
    <button>Create class</button>
   </form>
   <section className="panel"><h2>Classes</h2>{classForm.academic_year_id?(classes.length?classes.map(x=><button type="button" className="simple-row" key={x.id} onClick={()=>{setSectionForm({class_id:x.id,name:""});loadSections(x.id)}}><strong>{x.name}</strong><span>Open sections →</span></button>):<p className="muted">No classes for this academic year yet.</p>):<p className="muted">Select an academic year.</p>}</section>
  </section>

  <section className="profile-grid" style={{marginTop:18}}>
   <form className="panel" onSubmit={createSection}><h2>3. Section</h2>
    <label>Class<select value={sectionForm.class_id} onChange={e=>{setSectionForm({class_id:e.target.value,name:""});loadSections(e.target.value)}} required><option value="">Select class</option>{classes.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <label>Section name<input placeholder="A" value={sectionForm.name} onChange={e=>setSectionForm({...sectionForm,name:e.target.value})} required/></label>
    <button>Create section</button>
   </form>
   <section className="panel"><h2>Sections</h2>{sectionForm.class_id?(sections.length?sections.map(x=><div className="simple-row" key={x.id}><strong>{x.name}</strong><span className="status-pill">ACTIVE</span></div>):<p className="muted">No sections for this class yet.</p>):<p className="muted">Select a class.</p>}</section>
  </section>

  <section className="panel settings-note"><h2>Next: student enrollment</h2><p className="muted">After the class and section are ready, open Students → Student 360 and enroll the student into this academic structure.</p><button onClick={()=>router.push("/students")}>Go to Students</button></section>
 </main>;
}

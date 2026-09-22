"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage(){
  const router=useRouter();
  const [institutionCode,setInstitutionCode]=useState("GAINT");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  async function submit(e:FormEvent){
    e.preventDefault(); setError(""); setLoading(true);
    try{
      const base=process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const r=await fetch(base+"/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({institution_code:institutionCode,email,password})});
      if(!r.ok) throw new Error("Invalid email or password");
      router.push("/dashboard");
    }catch(e){setError(e instanceof Error?e.message:"Login failed");}
    finally{setLoading(false);}
  }
  return <main className="auth-shell"><form className="auth-card" onSubmit={submit}>
    <div className="brand-mark">GA</div><p className="eyebrow">GAINT ACADEMY</p>
    <h1>Welcome back</h1><p className="muted">Sign in to your institution workspace.</p>
    <label>Institution code<input value={institutionCode} onChange={e=>setInstitutionCode(e.target.value.toUpperCase())} required autoComplete="organization"/></label>
    <label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required autoComplete="email"/></label>
    <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="current-password"/></label>
    <p className="auth-link"><Link href="/forgot-password">Forgot password?</Link></p>
    {error&&<p className="error">{error}</p>}<button disabled={loading}>{loading?"Signing in…":"Sign in"}</button>
    <p className="secure-note">Tenant-aware secure access • GAINT Academy</p>
  </form></main>;
}

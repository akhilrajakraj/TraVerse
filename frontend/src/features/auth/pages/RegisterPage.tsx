import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { ErrorState } from "../../../components/ui/ErrorState";
import { useAuth } from "../hooks/useAuth";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ firstName: "", lastName: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null); setSubmitting(true);
    try { await register(form.email, form.password, form.firstName, form.lastName); navigate("/dashboard", { replace: true }); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "We couldn't create your account. Please try again."); }
    finally { setSubmitting(false); }
  }

  return <main className="auth-page"><div className="auth-card"><Link to="/" className="auth-brand"><span className="brand-mark">T</span>TraVerse</Link><h1>Start your journey</h1><p>Create your account and let TraVerse handle the planning details.</p>
    {error && <ErrorState message={error} />}
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-two-col"><Input label="First name" required value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} /><Input label="Last name" required value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} /></div>
      <Input label="Email" type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <Input label="Password" type="password" required minLength={8} autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
      <Button type="submit" isLoading={submitting}>Create account</Button>
    </form>
    <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
  </div></main>;
}

export function AuthLayout({ children }: { children: ReactNode }) { return <main className="auth-page">{children}</main>; }

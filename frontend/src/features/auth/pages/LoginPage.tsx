import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { ErrorState } from "../../../components/ui/ErrorState";
import { ApiRequestError } from "../../../lib/apiClient";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null); setSubmitting(true);
    try { await login(email, password); navigate("/dashboard", { replace: true }); }
    catch (cause) { setError(cause instanceof ApiRequestError && cause.status === 400 ? "Email or password is incorrect." : "We couldn't sign you in. Please try again."); }
    finally { setSubmitting(false); }
  }

  return <AuthShell title="Welcome back" subtitle="Continue planning your next journey.">
    {error && <ErrorState message={error} />}
    <form className="auth-form" onSubmit={submit}>
      <Input label="Email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input label="Password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button type="submit" isLoading={submitting}>Sign in</Button>
    </form>
    <p className="auth-switch">New to TraVerse? <Link to="/register">Create an account</Link></p>
  </AuthShell>;
}

function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <main className="auth-page"><div className="auth-card"><Link to="/" className="auth-brand"><span className="brand-mark">T</span>TraVerse</Link><h1>{title}</h1><p>{subtitle}</p>{children}</div></main>;
}

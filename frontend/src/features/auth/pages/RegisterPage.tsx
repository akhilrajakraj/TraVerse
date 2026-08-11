import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { ErrorState } from "../../../components/ui/ErrorState";
import { ApiRequestError } from "../../../lib/apiClient";
import { useAuth } from "../hooks/useAuth";

export function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ firstName: "", lastName: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [registered, setRegistered] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form.email, form.password, form.firstName, form.lastName);
      setRegistered(true);
    } catch (cause) {
      if (cause instanceof ApiRequestError && cause.status === 400) {
        setError(cause.message || "This email may already be registered. Please check your details.");
      } else {
        setError(cause instanceof Error ? cause.message : "We couldn't create your account. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (registered) {
    return (
      <main className="auth-page">
        <div className="auth-card auth-success-card">
          <Link to="/" className="auth-brand"><span className="brand-mark">T</span>TraVerse</Link>
          <div className="success-mark" aria-hidden="true">✓</div>
          <span className="section-kicker">Account created</span>
          <h1>Welcome to TraVerse.</h1>
          <p>Your account has been created successfully. Sign in when you're ready and we'll take you to your travel workspace.</p>
          <div className="success-actions">
            <Link to="/login" className="success-primary">Sign in</Link>
            <Link to="/" className="success-secondary">Return home</Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-brand"><span className="brand-mark">T</span>TraVerse</Link>
        <h1>Start your journey</h1>
        <p>Create your account and let TraVerse handle the planning details.</p>
        {error && <ErrorState message={error} />}
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-two-col">
            <Input label="First name" required value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} autoComplete="given-name" />
            <Input label="Last name" required value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} autoComplete="family-name" />
          </div>
          <Input label="Email" type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input label="Password" type="password" required minLength={8} autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <Button type="submit" isLoading={submitting}>Create account</Button>
        </form>
        <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
      </div>
    </main>
  );
}

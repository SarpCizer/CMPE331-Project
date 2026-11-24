import { useState } from "react";
import { createApi } from "../api";
import Brand from "../components/Brand";
import FieldError from "../components/FieldError";
import ProduceArt from "../components/ProduceArt";
import { focusInvalid } from "../utils/forms";

export default function Auth({ onSession, notice }) {
  const [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(notice || ""),
    [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setError("");
    const form = event.currentTarget,
      fields = new FormData(form),
      email = fields.get("email").trim(),
      password = fields.get("password");
    const invalid = {};
    if (!email || form.elements.email.validity.typeMismatch)
      invalid.email = "Enter a valid email address.";
    if (!password || (register && [...password].length < 8))
      invalid.password = register
        ? "Use at least 8 characters for your password."
        : "Enter your password.";
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(form, invalid);
      return;
    }
    setBusy(true);
    try {
      const api = createApi();
      if (register)
        await api("/accounts", { method: "POST", body: { email, password } });
      const result = await api("/sessions", {
        method: "POST",
        body: { email, password },
      });
      onSession({ email: email.toLowerCase(), token: result.token });
    } catch (error) {
      if (error.status === 409) {
        setErrors({ email: error.message });
        form.elements.email.focus();
      } else
        setError(
          error.status === 401
            ? "Email or password is incorrect. Please try again."
            : error.message,
        );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-layout">
      <section className="auth-story" aria-labelledby="auth-story-title">
        <Brand />
        <div className="auth-copy">
          <span className="eyebrow">A LITTLE LESS WASTE</span>
          <h1 id="auth-story-title">
            Good things
            <br />
            start in
            <br />
            <em>your fridge.</em>
          </h1>
          <p>
            Make room for better meals. Keep track of what you have and find a
            little inspiration for what comes next.
          </p>
          <ProduceArt />
        </div>
        <span className="auth-footer">
          A thoughtful kitchen, one ingredient at a time.
        </span>
      </section>
      <main className="auth-main">
        <div className="auth-card">
          <span className="eyebrow">YOUR KITCHEN COMPANION</span>
          <h2>{register ? "A fresh start." : "Welcome back."}</h2>
          <p>
            {register
              ? "Create an account and make the most of what you have."
              : "Sign in to your own little corner of the kitchen."}
          </p>
          <form
            noValidate
            onSubmit={submit}
            aria-describedby={error ? "auth-error" : undefined}
          >
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength="254"
              placeholder="you@example.com"
              disabled={busy}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
              onChange={() => setErrors((value) => ({ ...value, email: "" }))}
            />
            <FieldError id="email-error">{errors.email}</FieldError>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 8 : 1}
              maxLength="1024"
              disabled={busy}
              aria-invalid={!!errors.password}
              aria-describedby={
                [
                  register && "password-help",
                  errors.password && "password-error",
                ]
                  .filter(Boolean)
                  .join(" ") || undefined
              }
              onChange={() =>
                setErrors((value) => ({ ...value, password: "" }))
              }
            />
            {register && (
              <small id="password-help">Use at least 8 characters.</small>
            )}
            <FieldError id="password-error">{errors.password}</FieldError>
            {error && (
              <p id="auth-error" className="error" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="primary auth-submit"
              disabled={busy}
            >
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            </button>
          </form>
          <p className="auth-switch">
            {register ? "Already have an account?" : "New to Fridgely?"}{" "}
            <button
              className="text-button"
              disabled={busy}
              onClick={() => {
                setRegister(!register);
                setError("");
                setErrors({});
              }}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
          <p>
            <a href="/api/docs">API documentation</a>
          </p>
        </div>
      </main>
    </div>
  );
}

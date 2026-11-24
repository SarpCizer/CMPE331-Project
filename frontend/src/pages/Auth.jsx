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
    <div className="grid min-h-screen grid-cols-[1fr_1fr] mobile:grid-cols-[1fr]">
      <section
        className="relative flex flex-col overflow-hidden bg-[#e2ede3] px-16 py-[50px] tablet:p-[35px] mobile:p-6"
        aria-labelledby="auth-story-title"
      >
        <Brand className="mobile:text-[1.6rem]" />
        <div className="relative mx-0 my-auto max-w-[500px] px-0 pt-[70px] pb-[110px] mobile:max-w-none mobile:pt-10 mobile:pb-[30px]">
          <span className="eyebrow">A LITTLE LESS WASTE</span>
          <h1
            id="auth-story-title"
            className="mb-6 font-serif text-[clamp(3.2rem,5vw,5.4rem)] leading-[1.03] font-normal tracking-[-0.055em] mobile:text-[3rem]"
          >
            Good things
            <br />
            start in
            <br />
            <em className="font-normal text-[#497353]">your fridge.</em>
          </h1>
          <p className="max-w-[340px] text-[1rem] mobile:max-w-[330px]">
            Make room for better meals. Keep track of what you have and find a
            little inspiration for what comes next.
          </p>
          <ProduceArt className="absolute -right-[25px] -bottom-[4px] w-[200px] tablet:-right-[10px] tablet:w-[165px] mobile:right-0 mobile:bottom-5 mobile:w-[130px] mobile:opacity-50" />
        </div>
        <span className="text-[0.85rem] text-[#536d59] mobile:hidden">
          A thoughtful kitchen, one ingredient at a time.
        </span>
      </section>
      <main className="flex items-center justify-center bg-[#fafbf8] px-8 py-[50px] mobile:px-6 mobile:pt-[35px] mobile:pb-[50px]">
        <div className="w-full max-w-[390px] mobile:max-w-[460px]">
          <span className="eyebrow">YOUR KITCHEN COMPANION</span>
          <h2 className="mb-[14px] text-[2.4rem] mobile:text-[2rem]">
            {register ? "A fresh start." : "Welcome back."}
          </h2>
          <p className="mb-[30px]">
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
              <small id="password-help" className="mt-[7px] block">
                Use at least 8 characters.
              </small>
            )}
            <FieldError id="password-error">{errors.password}</FieldError>
            {error && (
              <p id="auth-error" className="alert-error" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="btn-primary mt-[26px] w-full"
              disabled={busy}
            >
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
            </button>
          </form>
          <p className="mt-[25px] mb-[30px] text-center text-[0.9rem]">
            {register ? "Already have an account?" : "New to Fridgely?"}{" "}
            <button
              className="btn-text"
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
          <p className="mb-[30px]">
            <a href="/api/docs">API documentation</a>
          </p>
        </div>
      </main>
    </div>
  );
}

import { useState } from "react";
import FieldError from "./FieldError";
import { focusInvalid } from "../utils/forms";

export default function ChangePassword({ api, run, clearSession }) {
  const [errors, setErrors] = useState({});
  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const currentPassword = fields.get("currentPassword"),
      newPassword = fields.get("newPassword"),
      confirmation = fields.get("confirmation");
    const invalid = {};
    if (!currentPassword) invalid.currentPassword = "Enter your current password.";
    if ([...newPassword].length < 12)
      invalid.newPassword = "Use at least 12 characters and a unique password.";
    else if (newPassword === currentPassword)
      invalid.newPassword = "Choose a different password.";
    if (confirmation !== newPassword)
      invalid.confirmation = "The new passwords do not match.";
    setErrors(invalid);
    if (Object.keys(invalid).length) {
      focusInvalid(form, invalid);
      return;
    }
    const result = await run(async () => {
      try {
        await api("/profile/password", {
          method: "PUT",
          body: { currentPassword, newPassword },
        });
        return true;
      } catch (error) {
        if (error.status === 400) {
          setErrors({ currentPassword: "Check your current password and try again." });
          return false;
        }
        throw error;
      }
    });
    if (result) {
      form.reset();
      clearSession("Password changed. Sign in with your new password.");
    }
  }
  return (
    <section className="panel mt-6 max-w-[750px]">
      <span className="eyebrow">ACCOUNT SECURITY</span>
      <h2>Change your password</h2>
      <p>
        If your browser warns about an exposed password, choose a new, unique
        password you do not use elsewhere. Changing it signs out your existing
        sessions and keeps your kitchen data.
      </p>
      <form className="mt-6" noValidate onSubmit={submit}>
        {[
          ["currentPassword", "Current password", "current-password"],
          ["newPassword", "New password", "new-password"],
          ["confirmation", "Confirm new password", "new-password"],
        ].map(([name, label, autoComplete]) => (
          <div key={name} className="mb-5">
            <label htmlFor={name}>{label}</label>
            <input
              id={name}
              name={name}
              type="password"
              autoComplete={autoComplete}
              maxLength={1024}
              minLength={name === "currentPassword" ? 1 : 12}
              required
              aria-invalid={!!errors[name]}
              aria-describedby={errors[name] ? `${name}-error` : undefined}
              onChange={() => setErrors((value) => ({ ...value, [name]: "" }))}
            />
            <FieldError id={`${name}-error`}>{errors[name]}</FieldError>
          </div>
        ))}
        <button className="btn-primary" type="submit">Change password</button>
      </form>
    </section>
  );
}

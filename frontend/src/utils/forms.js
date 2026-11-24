export function focusInvalid(form, errors) {
  form.querySelector(`#${Object.keys(errors)[0]}`)?.focus();
}
export function nameError(value, label) {
  return value.trim() ? "" : `Enter ${label} before adding it.`;
}
export function splitPreferences(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
export function preferenceError(values) {
  if (values.length > 100) return "Use at most 100 entries in this field.";
  if (values.some((value) => [...value].length > 128))
    return "Use at most 128 characters per entry.";
  return "";
}

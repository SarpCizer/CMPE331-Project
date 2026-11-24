export function savedSession() {
  try {
    const value = JSON.parse(sessionStorage.getItem("fridgely.session"));
    return typeof value?.token === "string" && typeof value?.email === "string"
      ? value
      : null;
  } catch {
    return null;
  }
}

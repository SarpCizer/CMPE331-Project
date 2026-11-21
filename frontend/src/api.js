export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function createApi(token, signal) {
  return async function request(path, { method = "GET", body } = {}) {
    let response;
    try {
      response = await fetch(`/api${path}`, {
        method,
        signal,
        cache: "no-store",
        redirect: "error",
        headers: {
          ...(body === undefined ? {} : { "Content-Type": "application/json" }),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new ApiError(
        "We could not reach Fridgely. Check your connection and try again.",
        0,
      );
    }
    if (response.status === 204) return null;
    let data;
    try {
      data = await response.json();
    } catch {
      throw new ApiError(
        "The service returned an unexpected response. Please try again.",
        response.status,
      );
    }
    if (!response.ok) {
      const message =
        response.status === 401
          ? "Your session ended. Please sign in again."
          : response.status === 409
            ? "An account already uses this email. Try signing in."
            : response.status === 503
              ? "The service is temporarily unavailable. Please try again."
              : response.status >= 500 || response.status === 422
                ? "The service could not complete this request. Please try again."
                : typeof data.error === "string"
                  ? data.error
                  : "This request could not be completed. Please try again.";
      throw new ApiError(message, response.status);
    }
    return data;
  };
}

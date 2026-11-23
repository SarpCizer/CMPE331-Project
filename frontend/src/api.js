import axios from "axios";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

// One shared Axios client for the same-origin FastAPI host. Responses are read
// as text and parsed here so malformed bodies produce a friendly error instead
// of being passed through silently.
export const client = axios.create({
  baseURL: "/api",
  adapter: "fetch",
  fetchOptions: { cache: "no-store", redirect: "error" },
  responseType: "text",
  transformResponse: [(body) => body],
  validateStatus: () => true,
});

// Attach the signed session token to every request that carries one.
client.interceptors.request.use((config) => {
  if (config.token) config.headers.Authorization = `Bearer ${config.token}`;
  return config;
});

function abortError() {
  const error = new Error("The request was cancelled.");
  error.name = "AbortError";
  return error;
}

function errorMessage(status, data) {
  if (status === 401) return "Your session ended. Please sign in again.";
  if (status === 409) return "An account already uses this email. Try signing in.";
  if (status === 503)
    return "The service is temporarily unavailable. Please try again.";
  if (status >= 500 || status === 422)
    return "The service could not complete this request. Please try again.";
  return typeof data?.error === "string"
    ? data.error
    : "This request could not be completed. Please try again.";
}

// Turn every completed HTTP exchange into parsed data or an ApiError with a
// safe, user-facing message. A 401 is surfaced so the app can end the session.
client.interceptors.response.use(
  (response) => {
    if (response.status === 204) return null;
    let data;
    try {
      data = JSON.parse(response.data);
    } catch {
      throw new ApiError(
        "The service returned an unexpected response. Please try again.",
        response.status,
      );
    }
    if (response.status < 200 || response.status >= 300)
      throw new ApiError(errorMessage(response.status, data), response.status);
    return data;
  },
  (error) => {
    if (axios.isCancel(error) || error?.name === "AbortError")
      throw abortError();
    throw new ApiError(
      "We could not reach Fridgely. Check your connection and try again.",
      0,
    );
  },
);

export function createApi(token, signal) {
  return function request(path, { method = "GET", body } = {}) {
    return client.request({
      url: path,
      method,
      signal,
      token,
      ...(body === undefined ? {} : { data: body }),
    });
  };
}

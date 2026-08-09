const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// The backend echoes the current csrf_token cookie value back as an X-CSRF-Token
// *response* header on every request (see backend/app/core/csrf.py). We read it from
// there rather than from document.cookie: cookies are only visible to JS on the domain
// that set them, so once frontend and backend are on different domains in production
// (e.g. Vercel calling Render), document.cookie can never see a cookie the backend set.
// Reading from a response header works identically same-site (dev) or cross-site (prod).
let cachedCsrfToken: string | null = null;

function captureCsrfToken(res: Response): void {
  const token = res.headers.get("X-CSRF-Token");
  if (token) cachedCsrfToken = token;
}

async function parseErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return String(body.detail[0].msg);
  } catch {
    // fall through to statusText
  }
  return res.statusText || "Request failed";
}

async function request<T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  if (typeof options.body === "string") headers.set("Content-Type", "application/json");
  // FormData bodies get no Content-Type here — the browser sets multipart/form-data
  // with the correct boundary itself; setting it manually breaks the boundary.
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && cachedCsrfToken) {
    headers.set("X-CSRF-Token", cachedCsrfToken);
  }

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  captureCsrfToken(res);

  if (res.status === 401 && !isRetry && path !== "/auth/refresh" && path !== "/auth/login") {
    const refreshHeaders = new Headers();
    if (cachedCsrfToken) refreshHeaders.set("X-CSRF-Token", cachedCsrfToken);
    const refreshed = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: refreshHeaders,
    });
    captureCsrfToken(refreshed);
    if (refreshed.ok) {
      return request<T>(path, options, true);
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, formData: FormData) => request<T>(path, { method: "POST", body: formData }),
};

/** Direct download URL for <a href> / window.open — the browser sends the auth cookie itself. */
export function downloadUrl(path: string): string {
  return `${API_URL}/api/v1${path}`;
}

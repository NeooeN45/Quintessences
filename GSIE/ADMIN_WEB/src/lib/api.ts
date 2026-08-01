/**
 * Client API GSIE — données réelles uniquement.
 *
 * Pas de mock, pas de fallback. Si l'API est indisponible, l'UI affiche
 * un message d'erreur clair. Aucune donnée inventée.
 *
 * Auth : JWT RS256 via /api/v1/auth/login. Tokens stockés en
 * sessionStorage (effacés à la fermeture de l'onglet).
 */

const API_URL = import.meta.env.PUBLIC_GSIE_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

// Exportés pour les composants qui font du fetch brut (WebSocket, etc.)
export { API_URL, API_PREFIX };

// --- Types ---

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
  dependencies: Record<string, string>;
}

export interface ResourceList {
  items: unknown[];
  total: number;
  page: number;
  page_size: number;
}

// --- Session management ---

const SESSION_KEY = "gsie_admin_session";

interface Session {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

function getSession(): Session | null {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const s = JSON.parse(raw) as Session;
    if (Date.now() > s.expiresAt) {
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    return s;
  } catch {
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function setSession(login: LoginResponse): Session {
  const session: Session = {
    accessToken: login.access_token,
    refreshToken: login.refresh_token,
    expiresAt: Date.now() + login.expires_in * 1000,
  };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
}

function getAuthHeader(): Record<string, string> {
  const session = getSession();
  if (!session) return {};
  return { Authorization: `Bearer ${session.accessToken}` };
}

/**
 * Fetch avec auth + refresh automatique sur 401.
 * Pour les composants qui ne peuvent pas utiliser `request` (WebSocket,
 * streaming, endpoints non-JSON). Retourne la Response brute.
 */
export async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_URL}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers as Record<string, string>),
  };

  let resp = await fetch(url, { ...options, headers });

  if (resp.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const newHeaders = { ...headers, ...getAuthHeader() };
      resp = await fetch(url, { ...options, headers: newHeaders });
    }
    if (resp.status === 401) {
      clearSession();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new ApiError(401, "Session expirée");
    }
  }

  return resp;
}

export { getAuthHeader };

// --- Fetch wrapper ---

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Token refresh : évite la redirection brutale sur 401
let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise;

  const session = getSession();
  if (!session?.refreshToken) return false;

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const resp = await fetch(`${API_URL}${API_PREFIX}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: session.refreshToken }),
      });
      if (!resp.ok) {
        clearSession();
        return false;
      }
      const data = await resp.json();
      setSession(data);
      return true;
    } catch {
      clearSession();
      return false;
    } finally {
      isRefreshing = false;
    }
  })();

  return refreshPromise;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith("/api/") || path.startsWith("/health") || path.startsWith("/ready")
    ? `${API_URL}${path}`
    : `${API_URL}${API_PREFIX}${path}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers as Record<string, string>),
  };

  let resp = await fetch(url, { ...options, headers });

  // 401 : tenter un refresh token avant d'abandonner
  if (resp.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Réessayer avec le nouveau token
      const newHeaders = { ...headers, ...getAuthHeader() };
      resp = await fetch(url, { ...options, headers: newHeaders });
    }

    if (resp.status === 401) {
      clearSession();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new ApiError(401, "Session expirée");
    }
  }

  // 429 : retry avec backoff exponentiel (max 1 retry)
  if (resp.status === 429) {
    const retryAfter = parseInt(resp.headers.get("Retry-After") ?? "2", 10);
    await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
    resp = await fetch(url, { ...options, headers });
  }

  if (!resp.ok) {
    let detail = `Erreur ${resp.status}`;
    let code: string | undefined;
    try {
      const body = await resp.json();
      detail = body.detail ?? body.title ?? detail;
      code = body.error_code;
    } catch {
      // corps non JSON
    }
    throw new ApiError(resp.status, detail, code);
  }

  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

// --- Auth ---

export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const resp = await request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setSession(resp);
  return resp;
}

export function logout(): void {
  clearSession();
}

export function isAuthenticated(): boolean {
  return getSession() !== null;
}

// --- Health ---

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getReady(): Promise<HealthResponse> {
  return request<HealthResponse>("/ready");
}

// --- Resources (métamodèle) ---

export async function getResourceTypes(): Promise<string[]> {
  const data = await request<{ types: string[] } | string[]>("/resources/types");
  return Array.isArray(data) ? data : data.types;
}

export async function getResources(
  type?: string,
  page = 1,
  pageSize = 20,
): Promise<ResourceList> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (type) params.set("type", type);
  return request<ResourceList>(`/resources?${params}`);
}

// --- Engines status ---

export interface EngineStatusResponse {
  engine: string;
  status: string;
  version?: string;
  message?: string;
}

export async function getEngineStatus(engine: string): Promise<EngineStatusResponse> {
  return request<EngineStatusResponse>(`/${engine}/status`);
}

export { ApiError };

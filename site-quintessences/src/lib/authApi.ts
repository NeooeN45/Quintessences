// Client minimal contre l'API GSIE réelle (IDENTITE-001). Les jetons
// sont stockés en sessionStorage — même choix qu'ADMIN_WEB, avec le
// même compromis documenté (SITE-001 §9) : à revoir avant une vraie
// ouverture publique de cette zone (httpOnly cookie serait plus sûr).
const API_BASE = "https://api.quintessences-platform.com/api/v1/auth";
const SESSION_KEY = "quintessences_session";

export interface Session {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Profile {
  account_id: string;
  display_name: string | null;
  email: string | null;
  email_verified: boolean;
  providers: string[];
  roles: string[];
}

export class AuthApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

function saveSession(session: Session) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getSession(): Session | null {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body?.detail === "string" ? body.detail : `Erreur ${res.status}`;
  } catch {
    return `Erreur ${res.status}`;
  }
}

export async function register(
  email: string,
  password: string,
  displayName?: string,
): Promise<Session> {
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName || null }),
  });
  if (!res.ok) throw new AuthApiError(await parseErrorDetail(res), res.status);
  const session = (await res.json()) as Session;
  saveSession(session);
  return session;
}

export async function loginPassword(
  email: string,
  password: string,
  turnstileToken: string,
): Promise<Session> {
  const res = await fetch(`${API_BASE}/login/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, turnstile_token: turnstileToken }),
  });
  if (!res.ok) throw new AuthApiError(await parseErrorDetail(res), res.status);
  const session = (await res.json()) as Session;
  saveSession(session);
  return session;
}

export async function getProfile(): Promise<Profile> {
  const session = getSession();
  if (!session) throw new AuthApiError("Non connecté", 401);
  const res = await fetch(`${API_BASE}/me`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!res.ok) throw new AuthApiError(await parseErrorDetail(res), res.status);
  return (await res.json()) as Profile;
}

export async function logout(): Promise<void> {
  const session = getSession();
  clearSession();
  if (!session) return;
  try {
    await fetch(`${API_BASE.replace("/auth", "")}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });
  } catch {
    // La session locale est déjà effacée — une erreur réseau ici ne
    // doit pas empêcher l'utilisateur de se considérer déconnecté.
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  ACCOUNT_ALREADY_EXISTS: "Un compte existe déjà avec cette adresse e-mail.",
  PASSWORD_COMPROMISED: "Ce mot de passe est connu comme compromis — choisissez-en un autre.",
  PASSWORD_TOO_WEAK: "Ce mot de passe est trop faible.",
};

export function friendlyErrorMessage(err: unknown): string {
  if (err instanceof AuthApiError) {
    return ERROR_MESSAGES[err.message] ?? "Identifiants invalides ou requête refusée.";
  }
  return "Une erreur réseau est survenue. Réessayez.";
}

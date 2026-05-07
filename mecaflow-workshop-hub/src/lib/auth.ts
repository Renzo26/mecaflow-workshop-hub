export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
  workshop_id: string;
}

export interface AuthWorkshop {
  id: string;
  name: string;
}

export interface AuthSession {
  user: AuthUser;
  workshop: AuthWorkshop;
  access_token: string;
}

export function setAuth(data: {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
  workshop: AuthWorkshop;
}) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("auth_user", JSON.stringify(data.user));
  localStorage.setItem("auth_workshop", JSON.stringify(data.workshop));
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("auth_user");
  localStorage.removeItem("auth_workshop");
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("access_token");
  const userRaw = localStorage.getItem("auth_user");
  const workshopRaw = localStorage.getItem("auth_workshop");
  if (!token || !userRaw || !workshopRaw) return null;
  try {
    return {
      access_token: token,
      user: JSON.parse(userRaw) as AuthUser,
      workshop: JSON.parse(workshopRaw) as AuthWorkshop,
    };
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

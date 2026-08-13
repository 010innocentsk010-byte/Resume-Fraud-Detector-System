"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, authApi, tokenStorage } from "./api";
import type { User, UserRole } from "./types";

interface DecodedAccessToken {
  sub: string;
  role: UserRole;
  exp: number;
}

function decodeToken(token: string): DecodedAccessToken | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

interface AuthContextValue {
  user: Pick<User, "id" | "role"> | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { name: string; email: string; password: string; organization?: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Pick<User, "id" | "role"> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Reads localStorage, unavailable during SSR — sync-on-mount is the
    // documented exception to "no setState in effects".
    const token = tokenStorage.access;
    if (token) {
      const decoded = decodeToken(token);
      if (decoded && decoded.exp * 1000 > Date.now()) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUser({ id: decoded.sub, role: decoded.role });
      } else {
        tokenStorage.clear();
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login(email, password);
      tokenStorage.set(tokens);
      const decoded = decodeToken(tokens.access_token);
      if (decoded) setUser({ id: decoded.sub, role: decoded.role });
      router.push("/dashboard");
    },
    [router]
  );

  const register = useCallback(
    async (payload: { name: string; email: string; password: string; organization?: string }) => {
      await authApi.register(payload);
      await login(payload.email, payload.password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    const refreshToken = tokenStorage.refresh;
    if (refreshToken) {
      // Best-effort server-side revocation — a network failure should never
      // block the user from clearing their local session.
      try {
        await authApi.logout(refreshToken);
      } catch {
        // ignore
      }
    }
    tokenStorage.clear();
    setUser(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: !!user, login, register, logout }),
    [user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

export { ApiError };

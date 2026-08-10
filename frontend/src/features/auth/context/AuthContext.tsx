import { createContext, useEffect, useState, type ReactNode } from "react";
import * as authApi from "../api/authApi";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../../../lib/apiClient";
import type { User } from "../api/authApi";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!getAccessToken()) {
      setIsLoading(false);
      return;
    }
    authApi.me().then(setUser).catch(() => clearTokens()).finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password);
    setTokens(tokens.access, tokens.refresh);
    setUser(await authApi.me());
  }

  async function register(email: string, password: string, firstName: string, lastName: string) {
    // Registration deliberately does not create a session. This keeps the
    // public registration success state deterministic and lets the user
    // explicitly choose when to sign in.
    await authApi.register(email, password, firstName, lastName);
  }

  async function logout() {
    try {
      if (getRefreshToken()) await authApi.logout();
    } catch {
      // Local logout must always succeed even when the server is unavailable.
    }
    clearTokens();
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, isAuthenticated: user !== null, isLoading, login, register, logout }}>{children}</AuthContext.Provider>;
}

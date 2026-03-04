/**
 * Auth API functions
 */

import client from "./client";
import type { User, AuthResponse } from "@/types";

export const authApi = {
  /**
   * Login with Google OAuth credential
   */
  googleLogin: (credential: string) =>
    client.post<AuthResponse>("/auth/google", { credential }),

  /**
   * Get current authenticated user
   */
  getMe: () => client.get<User>("/auth/me"),

  /**
   * Logout and clear session
   */
  logout: () => client.post("/auth/logout"),
};

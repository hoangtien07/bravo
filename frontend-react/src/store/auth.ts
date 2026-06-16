import { create } from "zustand";
import { api, auth as tokenStore, login as apiLogin } from "@/api/client";
import type { Identity } from "@/api/types";

interface AuthState {
  identity: Identity | null;
  loading: boolean;
  loadMe: () => Promise<void>;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  identity: null,
  loading: false,
  loadMe: async () => {
    if (!tokenStore.get()) return;
    set({ loading: true });
    try {
      const me = await api<Identity>("/api/me");
      set({ identity: me });
    } catch {
      tokenStore.clear();
      set({ identity: null });
    } finally {
      set({ loading: false });
    }
  },
  login: async (u, p) => {
    await apiLogin(u, p);
    const me = await api<Identity>("/api/me");
    set({ identity: me });
  },
  logout: () => {
    tokenStore.clear();
    set({ identity: null });
  },
}));

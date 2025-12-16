import { create } from 'zustand';
import type { Sandbox } from '@/api/types';

interface SandboxStore {
  sandboxes: Sandbox[];
  selectedSandboxId: string | null;
  isLoading: boolean;
  error: string | null;
  
  setSandboxes: (sandboxes: Sandbox[]) => void;
  addSandbox: (sandbox: Sandbox) => void;
  updateSandbox: (sandboxId: string, updates: Partial<Sandbox>) => void;
  removeSandbox: (sandboxId: string) => void;
  selectSandbox: (sandboxId: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSandboxStore = create<SandboxStore>((set) => ({
  sandboxes: [],
  selectedSandboxId: null,
  isLoading: false,
  error: null,

  setSandboxes: (sandboxes) => set({ sandboxes }),
  
  addSandbox: (sandbox) =>
    set((state) => ({ sandboxes: [...state.sandboxes, sandbox] })),
  
  updateSandbox: (sandboxId, updates) =>
    set((state) => ({
      sandboxes: state.sandboxes.map((s) =>
        s.id === sandboxId ? { ...s, ...updates } : s
      ),
    })),
  
  removeSandbox: (sandboxId) =>
    set((state) => ({
      sandboxes: state.sandboxes.filter((s) => s.id !== sandboxId),
    })),
  
  selectSandbox: (sandboxId) => set({ selectedSandboxId: sandboxId }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
}));


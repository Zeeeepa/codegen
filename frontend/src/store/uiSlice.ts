import { StateCreator } from 'zustand';

/**
 * UI Slice - Manages UI state (modals, selections, view preferences)
 * This slice does NOT persist to localStorage
 */
export interface UISlice {
  // Modal states
  isSettingsOpen: boolean;
  isChainDialogOpen: boolean;
  isWorkflowDialogOpen: boolean;
  
  // Selection states
  selectedWorkflowId: string | null;
  selectedChainId: number | null;
  selectedRunId: string | null;
  
  // View preferences
  activeTab: 'chains' | 'runs' | 'visual-editor';
  sidebarCollapsed: boolean;
  
  // Actions
  openSettings: () => void;
  closeSettings: () => void;
  toggleSettings: () => void;
  
  openChainDialog: () => void;
  closeChainDialog: () => void;
  
  openWorkflowDialog: () => void;
  closeWorkflowDialog: () => void;
  
  setSelectedWorkflow: (id: string | null) => void;
  setSelectedChain: (id: number | null) => void;
  setSelectedRun: (id: string | null) => void;
  
  setActiveTab: (tab: 'chains' | 'runs' | 'visual-editor') => void;
  toggleSidebar: () => void;
  
  resetUI: () => void;
}

export const createUISlice: StateCreator<UISlice> = (set) => ({
  // Initial state
  isSettingsOpen: false,
  isChainDialogOpen: false,
  isWorkflowDialogOpen: false,
  
  selectedWorkflowId: null,
  selectedChainId: null,
  selectedRunId: null,
  
  activeTab: 'visual-editor',
  sidebarCollapsed: false,

  // Modal actions
  openSettings: () => set({ isSettingsOpen: true }),
  closeSettings: () => set({ isSettingsOpen: false }),
  toggleSettings: () => set((state) => ({ isSettingsOpen: !state.isSettingsOpen })),
  
  openChainDialog: () => set({ isChainDialogOpen: true }),
  closeChainDialog: () => set({ isChainDialogOpen: false }),
  
  openWorkflowDialog: () => set({ isWorkflowDialogOpen: true }),
  closeWorkflowDialog: () => set({ isWorkflowDialogOpen: false }),

  // Selection actions
  setSelectedWorkflow: (id) => set({ selectedWorkflowId: id }),
  setSelectedChain: (id) => set({ selectedChainId: id }),
  setSelectedRun: (id) => set({ selectedRunId: id }),

  // View actions
  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  // Reset UI state
  resetUI: () => set({
    isSettingsOpen: false,
    isChainDialogOpen: false,
    isWorkflowDialogOpen: false,
    selectedWorkflowId: null,
    selectedChainId: null,
    selectedRunId: null,
    activeTab: 'visual-editor',
    sidebarCollapsed: false,
  }),
});


/**
 * Profile Management Store Slice
 * Feature 1: Basic Profile CRUD with localStorage persistence
 */

import { StateCreator } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import {
  Profile,
  ProfileSchema,
  CreateProfileInput,
  UpdateProfileInput,
  validateCreateProfileInput,
  validateUpdateProfileInput,
} from '@/schemas/profiles';

// ============================================================================
// State Interface
// ============================================================================

export interface ProfileSlice {
  profiles: Profile[];
  activeProfileId: string | null;
  
  // Actions
  createProfile: (input: CreateProfileInput) => Profile;
  updateProfile: (input: UpdateProfileInput) => void;
  deleteProfile: (id: string) => void;
  getProfile: (id: string) => Profile | undefined;
  getAllProfiles: () => Profile[];
  setActiveProfile: (id: string | null) => void;
  getActiveProfile: () => Profile | undefined;
}

// ============================================================================
// Slice Implementation
// ============================================================================

export const createProfileSlice: StateCreator<ProfileSlice> = (set, get) => ({
  profiles: [],
  activeProfileId: null,

  createProfile: (input) => {
    // Validate input
    const validation = validateCreateProfileInput(input);
    if (!validation.success) {
      console.error('Profile validation failed:', validation.error);
      throw new Error('Invalid profile data');
    }

    const now = Date.now();
    const newProfile: Profile = {
      ...validation.data,
      id: uuidv4(),
      createdAt: now,
      updatedAt: now,
    };

    // Validate complete profile
    const profileValidation = ProfileSchema.safeParse(newProfile);
    if (!profileValidation.success) {
      console.error('Profile schema validation failed:', profileValidation.error);
      throw new Error('Invalid profile schema');
    }

    set((state) => ({
      profiles: [...state.profiles, newProfile],
    }));

    return newProfile;
  },

  updateProfile: (input) => {
    // Validate input
    const validation = validateUpdateProfileInput(input);
    if (!validation.success) {
      console.error('Update validation failed:', validation.error);
      throw new Error('Invalid update data');
    }

    set((state) => {
      const profileIndex = state.profiles.findIndex((p) => p.id === input.id);
      if (profileIndex === -1) {
        console.warn(`Profile not found: ${input.id}`);
        return state;
      }

      const updatedProfiles = [...state.profiles];
      updatedProfiles[profileIndex] = {
        ...updatedProfiles[profileIndex],
        ...input,
        updatedAt: Date.now(),
      };

      // Validate updated profile
      const profileValidation = ProfileSchema.safeParse(updatedProfiles[profileIndex]);
      if (!profileValidation.success) {
        console.error('Updated profile validation failed:', profileValidation.error);
        return state; // Don't update if validation fails
      }

      return { profiles: updatedProfiles };
    });
  },

  deleteProfile: (id) => {
    set((state) => {
      const newState: Partial<ProfileSlice> = {
        profiles: state.profiles.filter((p) => p.id !== id),
      };

      // If deleted profile was active, clear active profile
      if (state.activeProfileId === id) {
        newState.activeProfileId = null;
      }

      return newState;
    });
  },

  getProfile: (id) => {
    return get().profiles.find((p) => p.id === id);
  },

  getAllProfiles: () => {
    return get().profiles;
  },

  setActiveProfile: (id) => {
    if (id === null) {
      set({ activeProfileId: null });
      return;
    }

    const profile = get().getProfile(id);
    if (!profile) {
      console.warn(`Cannot set active profile: ${id} not found`);
      return;
    }

    set({ activeProfileId: id });
  },

  getActiveProfile: () => {
    const { activeProfileId, profiles } = get();
    if (!activeProfileId) return undefined;
    return profiles.find((p) => p.id === activeProfileId);
  },
});


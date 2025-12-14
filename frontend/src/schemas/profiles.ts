/**
 * Zod Schemas for Agentic Profile System
 * Feature 1: Basic Profile CRUD
 */

import { z } from 'zod';

// ============================================================================
// Profile Schemas - Feature 1 (Minimal)
// ============================================================================

/**
 * Role enum for predefined agent roles
 */
export const ProfileRoleSchema = z.enum([
  'researcher',
  'developer',
  'analyst',
  'qa-engineer',
  'devops',
  'security',
  'api-manager',
  'custom'
]);

/**
 * Core profile schema with basic fields
 */
export const ProfileSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(50),
  description: z.string().max(500),
  role: ProfileRoleSchema,
  customRole: z.string().max(50).optional(), // Used when role is 'custom'
  isActive: z.boolean().default(false),
  createdAt: z.number(),
  updatedAt: z.number(),
});

/**
 * Profile creation input (without id and timestamps)
 */
export const CreateProfileInputSchema = ProfileSchema.omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

/**
 * Profile update input (partial fields except id)
 */
export const UpdateProfileInputSchema = ProfileSchema.partial().required({ id: true });

// ============================================================================
// Type Exports
// ============================================================================

export type Profile = z.infer<typeof ProfileSchema>;
export type ProfileRole = z.infer<typeof ProfileRoleSchema>;
export type CreateProfileInput = z.infer<typeof CreateProfileInputSchema>;
export type UpdateProfileInput = z.infer<typeof UpdateProfileInputSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Validate profile data
 */
export const validateProfile = (data: unknown) => {
  return ProfileSchema.safeParse(data);
};

/**
 * Validate create profile input
 */
export const validateCreateProfileInput = (data: unknown) => {
  return CreateProfileInputSchema.safeParse(data);
};

/**
 * Validate update profile input
 */
export const validateUpdateProfileInput = (data: unknown) => {
  return UpdateProfileInputSchema.safeParse(data);
};

/**
 * Role display names
 */
export const ROLE_DISPLAY_NAMES: Record<ProfileRole, string> = {
  researcher: 'Research Specialist',
  developer: 'Software Developer',
  analyst: 'Data Analyst',
  'qa-engineer': 'QA Engineer',
  devops: 'DevOps Engineer',
  security: 'Security Analyst',
  'api-manager': 'API Manager',
  custom: 'Custom Role'
};


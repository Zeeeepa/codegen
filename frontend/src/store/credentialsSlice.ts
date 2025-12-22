import { StateCreator } from 'zustand';
import {
  ApiCredentialsSchema,
  ApiValidationResultSchema,
  type ApiCredentials,
  type ApiValidationResult,
  safeParse,
} from '../schemas';

/**
 * Credentials Slice - Manages API credentials and validation state
 */
export interface CredentialsSlice {
  // State
  apiToken: string;
  organizationId: string;
  isValidated: boolean;
  validationResult: ApiValidationResult | null;
  
  // Actions
  setCredentials: (credentials: Partial<ApiCredentials>) => void;
  validateCredentials: (result: ApiValidationResult) => void;
  clearCredentials: () => void;
  getCredentials: () => ApiCredentials | null;
}

export const createCredentialsSlice: StateCreator<CredentialsSlice> = (set, get) => ({
  // Initial state
  apiToken: '',
  organizationId: '',
  isValidated: false,
  validationResult: null,

  // Set credentials with Zod validation
  setCredentials: (credentials) => {
    const current = get();
    const updated = {
      apiToken: credentials.apiToken ?? current.apiToken,
      organizationId: credentials.organizationId ?? current.organizationId,
    };

    // Validate with Zod schema
    const result = safeParse(ApiCredentialsSchema, updated);
    
    if (result.success) {
      set({
        apiToken: result.data.apiToken,
        organizationId: result.data.organizationId,
      });
    } else {
      console.error('Invalid credentials:', result.error);
      throw new Error(`Validation failed: ${result.error.message}`);
    }
  },

  // Update validation result
  validateCredentials: (result) => {
    const validated = safeParse(ApiValidationResultSchema, result);
    if (validated.success) {
      set({
        isValidated: validated.data.valid,
        validationResult: validated.data,
      });
    }
  },

  // Clear all credentials
  clearCredentials: () => {
    set({
      apiToken: '',
      organizationId: '',
      isValidated: false,
      validationResult: null,
    });
  },

  // Get validated credentials or null
  getCredentials: () => {
    const { apiToken, organizationId } = get();
    const result = safeParse(ApiCredentialsSchema, { apiToken, organizationId });
    return result.success ? result.data : null;
  },
});


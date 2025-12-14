/**
 * Profile Management Component
 * Feature 1: Basic Profile CRUD UI
 */

import React, { useState } from 'react';
import { useAppStore } from '@/store';
import { CreateProfileInput, ROLE_DISPLAY_NAMES, ProfileRole } from '@/schemas/profiles';
import { Plus, Edit2, Trash2, Check } from 'lucide-react';

export const ProfileManagement: React.FC = () => {
  const {
    profiles,
    activeProfileId,
    createProfile,
    updateProfile,
    deleteProfile,
    setActiveProfile,
  } = useAppStore();

  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateProfileInput>({
    name: '',
    description: '',
    role: 'developer' as ProfileRole,
    isActive: false,
  });
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      role: 'developer',
      isActive: false,
    });
    setError(null);
  };

  const handleCreate = () => {
    setError(null);
    try {
      if (!formData.name.trim()) {
        setError('Name is required');
        return;
      }
      
      const newProfile = createProfile(formData);
      setIsCreating(false);
      resetForm();
      console.log('Profile created:', newProfile);
    } catch (err: any) {
      setError(err.message || 'Failed to create profile');
      console.error('Create profile error:', err);
    }
  };

  const handleUpdate = () => {
    if (!editingId) return;
    
    setError(null);
    try {
      if (!formData.name.trim()) {
        setError('Name is required');
        return;
      }

      updateProfile({
        id: editingId,
        ...formData,
      });
      setEditingId(null);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
      console.error('Update profile error:', err);
    }
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this profile?')) {
      deleteProfile(id);
    }
  };

  const startEdit = (id: string) => {
    const profile = profiles.find((p) => p.id === id);
    if (!profile) return;

    setFormData({
      name: profile.name,
      description: profile.description,
      role: profile.role,
      customRole: profile.customRole,
      isActive: profile.isActive,
    });
    setEditingId(id);
    setIsCreating(false);
  };

  const cancelEdit = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Agent Profiles</h2>
        {!isCreating && !editingId && (
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            data-testid="create-profile-button"
          >
            <Plus size={20} />
            New Profile
          </button>
        )}
      </div>

      {/* Create/Edit Form */}
      {(isCreating || editingId) && (
        <div className="mb-6 p-4 border rounded bg-gray-50" data-testid="profile-form">
          <h3 className="text-lg font-semibold mb-4">
            {editingId ? 'Edit Profile' : 'Create New Profile'}
          </h3>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded" data-testid="form-error">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded"
                placeholder="e.g., PubMed Researcher"
                maxLength={50}
                data-testid="profile-name-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded"
                placeholder="Describe this agent's purpose..."
                rows={3}
                maxLength={500}
                data-testid="profile-description-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as ProfileRole })}
                className="w-full px-3 py-2 border rounded"
                data-testid="profile-role-select"
              >
                {Object.entries(ROLE_DISPLAY_NAMES).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {formData.role === 'custom' && (
              <div>
                <label className="block text-sm font-medium mb-1">Custom Role Name</label>
                <input
                  type="text"
                  value={formData.customRole || ''}
                  onChange={(e) => setFormData({ ...formData, customRole: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="e.g., Product Manager"
                  maxLength={50}
                  data-testid="profile-custom-role-input"
                />
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={editingId ? handleUpdate : handleCreate}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                data-testid="save-profile-button"
              >
                {editingId ? 'Update' : 'Create'}
              </button>
              <button
                onClick={cancelEdit}
                className="bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded"
                data-testid="cancel-profile-button"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Profiles List */}
      <div className="space-y-3" data-testid="profiles-list">
        {profiles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No profiles yet. Create your first agent profile!
          </div>
        ) : (
          profiles.map((profile) => (
            <div
              key={profile.id}
              className={`p-4 border rounded ${
                profile.id === activeProfileId ? 'border-blue-500 bg-blue-50' : 'bg-white'
              }`}
              data-testid={`profile-item-${profile.id}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold" data-testid={`profile-name-${profile.id}`}>
                      {profile.name}
                    </h3>
                    {profile.id === activeProfileId && (
                      <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded">
                        Active
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-1">
                    {ROLE_DISPLAY_NAMES[profile.role]}
                    {profile.role === 'custom' && profile.customRole && ` - ${profile.customRole}`}
                  </p>
                  
                  {profile.description && (
                    <p className="text-sm text-gray-700 mt-2">{profile.description}</p>
                  )}
                  
                  <p className="text-xs text-gray-400 mt-2">
                    Created: {new Date(profile.createdAt).toLocaleString()}
                  </p>
                </div>

                <div className="flex gap-2 ml-4">
                  {profile.id !== activeProfileId && (
                    <button
                      onClick={() => setActiveProfile(profile.id)}
                      className="p-2 text-green-600 hover:bg-green-100 rounded"
                      title="Set as active"
                      data-testid={`activate-profile-${profile.id}`}
                    >
                      <Check size={18} />
                    </button>
                  )}
                  
                  <button
                    onClick={() => startEdit(profile.id)}
                    className="p-2 text-blue-600 hover:bg-blue-100 rounded"
                    title="Edit"
                    data-testid={`edit-profile-${profile.id}`}
                  >
                    <Edit2 size={18} />
                  </button>
                  
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="p-2 text-red-600 hover:bg-red-100 rounded"
                    title="Delete"
                    data-testid={`delete-profile-${profile.id}`}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};


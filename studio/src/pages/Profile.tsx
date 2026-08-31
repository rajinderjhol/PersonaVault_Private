import React, { useState, useEffect } from 'react';
import { useUserQuery, useUpdateUserMutation } from '../hooks/query/useUserQuery';

export const Profile: React.FC = () => {
  const { data, isLoading, error } = useUserQuery();
  const updateMutation = useUpdateUserMutation();
  const [formData, setFormData] = useState({ name: '', email: '' });

  useEffect(() => {
    if (data) {
      setFormData({ name: data.name || '', email: data.email || '' });
    }
  }, [data]);

  if (isLoading) return <div>Loading Profile...</div>;
  if (error) return <div>Error loading Profile: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  const handleUpdate = () => {
    updateMutation.mutate(formData);
  };

  return (
    <div className="profile-container">
      <h1>User Profile</h1>
      <div className="profile-content">
        <label>
          Name:
          <input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
        </label>
        <br />
        <label>
          Email:
          <input value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
        </label>
        <br />
        <button onClick={handleUpdate} disabled={updateMutation.isPending}>
          {updateMutation.isPending ? 'Updating...' : 'Update Profile'}
        </button>
      </div>
    </div>
  );
};

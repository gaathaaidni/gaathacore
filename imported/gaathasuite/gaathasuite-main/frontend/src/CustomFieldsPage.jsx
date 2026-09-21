import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const CustomFieldsPage = () => {
  const { authFetch, user } = useAuth();
  const [customFields, setCustomFields] = useState({});
  const [status, setStatus] = useState({ type: '', message: '' });
  const [isSaving, setIsSaving] = useState(false);

  const canEditCustomFieldKeys = user?.role === 'orgadmin' || user?.role === 'superadmin' || user?.role === 'super_admin';
  const availableRoles = ['user', 'manager', 'lead', 'orgadmin', 'auditor'];

  useEffect(() => {
    authFetch('/api/superadmin/settings')
      .then(res => res?.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setCustomFields(data.custom_fields || {});
        }
      });
  }, [authFetch]);

  const handleSave = async () => {
    setIsSaving(true);
    setStatus({ type: 'info', message: 'Saving custom fields...' });
    const response = await authFetch('/api/superadmin/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ custom_fields: customFields }),
    });
    setIsSaving(false);
    if (response?.ok) {
      setStatus({ type: 'success', message: 'Custom fields saved successfully.' });
    } else {
      setStatus({ type: 'error', message: 'Failed to save custom fields.' });
    }
  };

  const handleFieldChange = (index, newKey, newValue) => {
    const oldKey = Object.keys(customFields)[index];
    const newFields = { ...customFields };
    const fieldData = newFields[oldKey];
    
    delete newFields[oldKey];
    newFields[newKey] = { ...fieldData, value: newValue };

    setCustomFields(newFields);
  };

  const handleRoleChange = (key, role) => {
    const roles = customFields[key]?.roles || [];
    const newRoles = roles.includes(role) ? roles.filter(r => r !== role) : [...roles, role];
    setCustomFields({ ...customFields, [key]: { ...customFields[key], roles: newRoles } });
  };

  const addField = () => {
    setCustomFields({ ...customFields, [`new_field_${Object.keys(customFields).length}`]: { value: '', roles: [] } });
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Custom Invoice Fields</h2>
          <p className="text-slate-500">Define custom key-value fields that appear on invoices.</p>
        </div>
        <button onClick={handleSave} disabled={isSaving} className="bg-blue-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50">
          {isSaving ? 'Saving...' : 'Save Fields'}
        </button>
      </div>

      {status.message && (
        <div className={`mb-6 p-4 rounded-lg text-sm ${status.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
          {status.message}
        </div>
      )}

      <div className="space-y-4">
        {Object.entries(customFields).map(([key, fieldData], index) => (
          <div key={index} className="p-4 border border-slate-200 rounded-lg bg-white">
            <div className="grid grid-cols-2 gap-4">
              <input type="text" value={key} onChange={(e) => handleFieldChange(index, e.target.value, fieldData.value)} className={`w-full p-2 border rounded ${!canEditCustomFieldKeys ? 'bg-slate-100' : ''}`} readOnly={!canEditCustomFieldKeys} />
              <input type="text" value={fieldData.value || ''} onChange={(e) => handleFieldChange(index, key, e.target.value)} className="w-full p-2 border rounded" placeholder="Default Value" />
            </div>
            {canEditCustomFieldKeys && (
              <div className="mt-3">
                <p className="text-xs text-slate-500 mb-1">Visible to roles:</p>
                <div className="flex flex-wrap gap-2">
                  {availableRoles.map(role => (
                    <label key={role} className="flex items-center gap-1.5 text-xs cursor-pointer"><input type="checkbox" checked={(fieldData.roles || []).includes(role)} onChange={() => handleRoleChange(key, role)} /> {role}</label>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {canEditCustomFieldKeys && <button onClick={addField} className="text-sm text-blue-600 hover:underline">+ Add Field</button>}
      </div>
    </div>
  );
};

export default CustomFieldsPage;
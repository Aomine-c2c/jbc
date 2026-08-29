'use client';

import React, { useState, useEffect } from 'react';
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Role {
  id: string;
  name: string;
}

interface Department {
  id: string;
  name: string;
}

export function UserFormDialog({ 
  user, 
  users,
  departments, 
  sections,
  teams,
  positions,
  roles, 
  onClose, 
  onSaved 
}: { 
  user?: any;
  users: any[];
  departments: any[]; 
  sections: any[];
  teams: any[];
  positions: any[];
  roles: {id: string, name: string}[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    password: '',
    department_id: user?.department_id || '',
    section_id: user?.section_id || '',
    team_id: user?.team_id || '',
    position_id: user?.position_id || '',
    supervisor_id: user?.supervisor_id || '',
    employee_number: user?.employee_number || '',
    shift_pattern: user?.shift_pattern || '',
    is_active: user !== undefined ? user.is_active : true,
  });

  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const isEditing = !!user;

  useEffect(() => {
    if (isEditing && user) {
      // Fetch user's current roles
      const fetchUserRoles = async () => {
        try {
          const userRoles = await apiFetch(`/api/v1/iam/users/${user.id}/roles`);
          if (userRoles) {
            setSelectedRoles(userRoles.map((r: Role) => r.id));
          }
        } catch (e) {
          console.error("Failed to fetch user roles", e);
        }
      };
      fetchUserRoles();
    }
  }, [user, isEditing]);

  const toggleRole = (roleId: string) => {
    setSelectedRoles(prev => 
      prev.includes(roleId) ? prev.filter(id => id !== roleId) : [...prev, roleId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      let savedUser: { id: string } | null = null;
      if (isEditing && user) {
        // Update user
        const updatePayload: Record<string, unknown> = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          department_id: formData.department_id || null,
          section_id: formData.section_id || null,
          team_id: formData.team_id || null,
          position_id: formData.position_id || null,
          supervisor_id: formData.supervisor_id || null,
          employee_number: formData.employee_number || null,
          shift_pattern: formData.shift_pattern || null,
          is_active: formData.is_active
        };
        savedUser = await apiFetch(`/api/v1/iam/users/${user.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatePayload)
        });
      } else {
        // Create user
        const createPayload = {
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          password: formData.password,
          department_id: formData.department_id || null,
          section_id: formData.section_id || null,
          team_id: formData.team_id || null,
          position_id: formData.position_id || null,
          supervisor_id: formData.supervisor_id || null,
          employee_number: formData.employee_number || null,
          shift_pattern: formData.shift_pattern || null,
        };
        savedUser = await apiFetch(`/api/v1/iam/users`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(createPayload)
        });
      }

      // If user was saved successfully, update roles
      if (savedUser && savedUser.id) {
        await apiFetch(`/api/v1/iam/users/${savedUser.id}/roles`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role_ids: selectedRoles })
        });
        onSaved();
      }
    } catch (error: unknown) {
      console.error(error);
      const err = error as { message?: string };
      alert(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card w-full max-w-xl rounded-xl shadow-lg border border-border flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-border flex justify-between items-center shrink-0">
          <h2 className="text-xl font-bold text-card-foreground">
            {isEditing ? 'Edit User' : 'Add New User'}
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            &times;
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto">
          <form id="user-form" onSubmit={handleSubmit} className="space-y-4">
            
            {!isEditing && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Email Address</label>
                <input 
                  type="email" required 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})}
                />
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">First Name</label>
                <input 
                  type="text" required 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Last Name</label>
                <input 
                  type="text" required 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})}
                />
              </div>
            </div>

            {!isEditing && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Temporary Password</label>
                <input 
                  type="password" required 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})}
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Department</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.department_id} onChange={e => setFormData({...formData, department_id: e.target.value})}
                >
                  <option value="">-- None --</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Section</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.section_id} 
                  onChange={e => setFormData({...formData, section_id: e.target.value})}
                  disabled={!formData.department_id}
                >
                  <option value="">-- None --</option>
                  {sections.filter(s => s.department_id === formData.department_id).map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-1">
                <label className="text-sm font-medium">Team</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.team_id} 
                  onChange={e => setFormData({...formData, team_id: e.target.value})}
                  disabled={!formData.section_id}
                >
                  <option value="">-- None --</option>
                  {teams.filter(t => t.section_id === formData.section_id).map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-1">
                <label className="text-sm font-medium">Position / Role</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.position_id} 
                  onChange={e => setFormData({...formData, position_id: e.target.value})}
                >
                  <option value="">-- None --</option>
                  {positions.filter(p => p.department_id === formData.department_id || !p.department_id).map(p => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-1">
                <label className="text-sm font-medium">Supervisor</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.supervisor_id} 
                  onChange={e => setFormData({...formData, supervisor_id: e.target.value})}
                >
                  <option value="">-- None --</option>
                  {users.filter(u => u.id !== user?.id).map(u => (
                    <option key={u.id} value={u.id}>{u.first_name} {u.last_name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Employee Number</label>
                <input 
                  type="text" 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.employee_number} 
                  onChange={e => setFormData({...formData, employee_number: e.target.value})}
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium">Shift Pattern</label>
                <select 
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  value={formData.shift_pattern} 
                  onChange={e => setFormData({...formData, shift_pattern: e.target.value})}
                >
                  <option value="">-- None --</option>
                  <option value="MORNING">Morning</option>
                  <option value="AFTERNOON">Afternoon</option>
                  <option value="NIGHT">Night</option>
                  <option value="ROTATING">Rotating</option>
                </select>
              </div>
            </div>

            {isEditing && (
              <div className="space-y-1">
                <label className="flex items-center space-x-2 text-sm font-medium cursor-pointer">
                  <input 
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={e => setFormData({...formData, is_active: e.target.checked})}
                    className="rounded border-input"
                  />
                  <span>Account is Active</span>
                </label>
              </div>
            )}

            <div className="pt-4 border-t border-border">
              <label className="text-sm font-bold mb-2 block">Assigned Roles</label>
              <div className="flex flex-wrap gap-2">
                {roles.map(role => {
                  const isSelected = selectedRoles.includes(role.id);
                  return (
                    <Badge 
                      key={role.id} 
                      variant={isSelected ? 'default' : 'outline'}
                      className="cursor-pointer text-xs py-1"
                      onClick={() => toggleRole(role.id)}
                    >
                      {role.name}
                    </Badge>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Click a role to toggle its assignment for this user.
              </p>
            </div>

          </form>
        </div>

        <div className="px-6 py-4 border-t border-border flex justify-end gap-3 shrink-0">
          <Button variant="outline" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" form="user-form" disabled={loading}>
            {loading ? 'Saving...' : 'Save User'}
          </Button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Protect } from "@/components/auth/Protect";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserFormDialog } from "@/components/users/UserFormDialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  department_id: string;
  department_name: string | null;
  roles: string[];
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<{ id: string; name: string }[]>([]);
  const [sections, setSections] = useState<{ id: string; name: string; department_id: string }[]>([]);
  const [teams, setTeams] = useState<{ id: string; name: string; section_id: string }[]>([]);
  const [positions, setPositions] = useState<{ id: string; title: string; department_id: string }[]>([]);
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);

  const loadData = () => {
    apiFetch("/api/v1/iam/users").then((data) => {
      if (data) setUsers(data);
    }).catch(console.error).finally(() => setLoading(false));

    apiFetch("/api/v1/iam/departments").then((data) => {
      if (data) setDepartments(data);
    }).catch(console.error);

    apiFetch("/api/v1/iam/org/sections").then((data) => {
      if (data) setSections(data);
    }).catch(console.error);

    apiFetch("/api/v1/iam/org/teams").then((data) => {
      if (data) setTeams(data);
    }).catch(console.error);

    apiFetch("/api/v1/iam/org/positions").then((data) => {
      if (data) setPositions(data);
    }).catch(console.error);

    apiFetch("/api/v1/iam/roles").then((data) => {
      if (data) setRoles(data);
    }).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddUser = () => {
    setEditingUser(undefined);
    setIsDialogOpen(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setIsDialogOpen(true);
  };

  const handleDialogSaved = () => {
    setIsDialogOpen(false);
    loadData();
  };

  const handleDeactivateUser = async (user: User) => {
    if (user.is_active === false) return; // already inactive
    const confirmed =
      typeof window === "undefined" ||
      window.confirm(`Deactivate ${user.first_name} ${user.last_name}? They will no longer be able to sign in.`);
    if (!confirmed) return;
    try {
      await apiFetch(`/api/v1/iam/users/${user.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: false }),
      });
      loadData();
    } catch (err) {
      console.error("Failed to deactivate user", err);
      if (typeof window !== "undefined") {
        window.alert("Failed to deactivate user. See console for details.");
      }
    }
  };

  return (
    <Protect capability="users:manage" isPageGuard moduleName="User Directory & IAM">
      <div className="space-y-6 p-4 md:p-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">User Management</h1>
          <Button onClick={handleAddUser} size="sm">
            Add User
          </Button>
        </div>

        {/* MOBILE USER CARDS (< md screens) */}
        <div className="md:hidden space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs text-muted-foreground">Loading users...</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">No users found.</div>
          ) : (
            users.map((user) => (
              <div key={user.id} className="p-4 bg-card border border-border rounded-xl shadow-xs space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-sm text-foreground">
                      {user.first_name} {user.last_name}
                    </div>
                    <div className="text-xs font-mono text-muted-foreground">{user.email}</div>
                  </div>
                  <Badge variant={user.is_active ? 'default' : 'destructive'} className="text-[10px]">
                    {user.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </div>

                <div className="text-xs text-muted-foreground">
                  <span className="font-semibold text-foreground">Department:</span> {user.department_name || 'None'}
                </div>

                <div className="flex flex-wrap gap-1">
                  {user.roles.length > 0 ? (
                    user.roles.map((r, idx) => (
                      <Badge key={idx} variant="secondary" className="text-[10px] px-1.5 py-0">
                        {r}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-muted-foreground text-xs italic">No roles</span>
                  )}
                </div>

                <div className="pt-2 border-t border-border/50 flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleEditUser(user)} className="text-xs">
                    Edit User
                  </Button>
                  {user.is_active && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs text-red-500 border-red-500/40 hover:bg-red-500/10"
                      onClick={() => handleDeactivateUser(user)}
                    >
                      Deactivate
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* DESKTOP TABLE VIEW (>= md screens) */}
        <div className="hidden md:block bg-card rounded-md border border-border overflow-hidden">
          <Table dense zebra>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    Loading users...
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    No users found.
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} className="hover:bg-muted/30">
                    <TableCell className="font-medium text-foreground">
                      {user.first_name} {user.last_name}
                    </TableCell>
                    <TableCell mono className="text-muted-foreground">{user.email}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.department_name || <span className="italic">None</span>}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {user.roles.length > 0 ? user.roles.map((r, idx) => (
                          <Badge key={idx} variant="secondary" className="text-[10px] px-1.5 py-0">
                            {r}
                          </Badge>
                        )) : <span className="text-muted-foreground text-xs italic">No roles</span>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'default' : 'destructive'}>
                        {user.is_active ? 'ACTIVE' : 'INACTIVE'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="xs" onClick={() => handleEditUser(user)}>
                          Edit
                        </Button>
                        {user.is_active && (
                          <Button
                            variant="ghost"
                            size="xs"
                            className="text-red-500 hover:text-red-400"
                            onClick={() => handleDeactivateUser(user)}
                          >
                            Deactivate
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {isDialogOpen && (
          <UserFormDialog 
            user={editingUser}
            users={users}
            departments={departments}
            sections={sections}
            teams={teams}
            positions={positions}
            roles={roles}
            onClose={() => setIsDialogOpen(false)}
            onSaved={handleDialogSaved}
          />
        )}
      </div>
    </Protect>
  );
}

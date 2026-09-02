/**
 * BIKITA DWRMS Enterprise Role-Based Access Control (RBAC) Engine
 * Strict capability matrix enforcing route guards, sidebar navigation, and multi-tier action authorizations.
 */

export type UserRole =
  | 'Operator'
  | 'Technician'
  | 'Supervisor'
  | 'Department Manager'
  | 'Safety Officer'
  | 'Administrator';

export interface RoleConfig {
  role: UserRole;
  title: string;
  defaultLandingRoute: string;
  allowedCapabilities: string[];
  deniedRoutes: string[];
}

export const ROLE_CONFIGS: Record<UserRole, RoleConfig> = {
  Operator: {
    role: 'Operator',
    title: 'Operator / Driver',
    defaultLandingRoute: '/my-work',
    allowedCapabilities: [
      'my_work:view',
      'job_card:create',
      'fleet:view',
      'requisition:create',
      'fleet_calendar:view',
    ],
    deniedRoutes: [
      '/dashboard',
      '/jobs',
      '/work',
      '/assets',
      '/materials',
      '/contractors',
      '/approvals',
      '/sla',
      '/admin',
    ],
  },
  Technician: {
    role: 'Technician',
    title: 'Technician / Artisan',
    defaultLandingRoute: '/my-work',
    allowedCapabilities: [
      'my_work:view',
      'jobs:view',
      'job_card:read',
      'job_card:create',
      'job_card:execute',
      'job_card:update',
      'fleet:view',
      'requisition:create',
      'fleet_calendar:view',
      'materials:view',
      'materials:request',
    ],
    deniedRoutes: [
      '/dashboard',
      '/work',
      '/assets',
      '/contractors',
      '/approvals',
      '/sla',
      '/admin',
    ],
  },
  Supervisor: {
    role: 'Supervisor',
    title: 'Supervisor / Shift Boss',
    defaultLandingRoute: '/dashboard',
    allowedCapabilities: [
      'my_work:view',
      'dashboard:view',
      'jobs:view',
      'job_card:read',
      'job_card:create',
      'job_card:execute',
      'job_card:update',
      'job_card:approve',
      'job_card:verify',
      'work_hub:view',
      'fleet:view',
      'fleet:allocate',
      'requisition:create',
      'requisition:approve',
      'fleet_calendar:view',
      'assets:view',
      'materials:view',
      'materials:approve',
      'contractors:view',
      'approvals:view',
      'sla:view',
    ],
    deniedRoutes: [
      '/admin/org',
      '/admin/locations',
      '/admin/workflows',
      '/admin/platform',
      '/admin/system',
      '/admin/users',
      '/admin/audit',
    ],
  },
  'Department Manager': {
    role: 'Department Manager',
    title: 'Dept Manager / Superintendent',
    defaultLandingRoute: '/dashboard',
    allowedCapabilities: [
      'my_work:view',
      'dashboard:view',
      'jobs:view',
      'job_card:read',
      'job_card:create',
      'job_card:execute',
      'job_card:update',
      'job_card:approve',
      'job_card:verify',
      'work_hub:view',
      'fleet:view',
      'fleet:allocate',
      'requisition:create',
      'requisition:approve',
      'fleet_calendar:view',
      'assets:view',
      'materials:view',
      'materials:approve',
      'contractors:view',
      'approvals:view',
      'sla:view',
      'org:manage',
      'locations:manage',
      'workflows:manage',
    ],
    deniedRoutes: [
      '/admin/platform',
      '/admin/system',
      '/admin/users',
      '/admin/audit',
    ],
  },
  'Safety Officer': {
    role: 'Safety Officer',
    title: 'Safety Officer (HSE)',
    defaultLandingRoute: '/dashboard',
    allowedCapabilities: [
      'my_work:view',
      'dashboard:view',
      'jobs:view',
      'job_card:read',
      'job_card:create',
      'job_card:execute',
      'work_hub:view',
      'fleet:view',
      'fleet_calendar:view',
      'assets:view',
      'contractors:view',
      'approvals:view',
      'sla:view',
      'audit:view',
    ],
    deniedRoutes: [
      '/materials',
      '/fleet/requisitions/new',
      '/admin/org',
      '/admin/locations',
      '/admin/workflows',
      '/admin/platform',
      '/admin/system',
      '/admin/users',
    ],
  },
  Administrator: {
    role: 'Administrator',
    title: 'Administrator',
    defaultLandingRoute: '/dashboard',
    allowedCapabilities: [
      'global_override',
      'my_work:view',
      'dashboard:view',
      'jobs:view',
      'job_card:read',
      'job_card:create',
      'job_card:execute',
      'job_card:update',
      'job_card:approve',
      'job_card:verify',
      'work_hub:view',
      'fleet:view',
      'fleet:allocate',
      'requisition:create',
      'requisition:approve',
      'fleet_calendar:view',
      'assets:view',
      'materials:view',
      'materials:approve',
      'materials:request',
      'contractors:view',
      'approvals:view',
      'sla:view',
      'org:manage',
      'locations:manage',
      'workflows:manage',
      'users:manage',
      'platform:manage',
      'system:manage',
      'audit:view',
    ],
    deniedRoutes: [],
  },
};

/**
 * Normalizes email or role string to one of the 6 canonical UserRole types
 */
export function resolveUserRole(roleOrEmail?: string | null): UserRole {
  if (!roleOrEmail) return 'Administrator';

  const text = roleOrEmail.toLowerCase().trim();

  if (text.includes('operator') || text.includes('driver') || text.includes('plant.op')) {
    return 'Operator';
  }
  if (text.includes('tech') || text.includes('artisan') || text.includes('elec.tech')) {
    return 'Technician';
  }
  if (text.includes('safety') || text.includes('hse')) {
    return 'Safety Officer';
  }
  if (text.includes('manager') || text.includes('superintendent') || text.includes('mechmgr')) {
    return 'Department Manager';
  }
  if (text.includes('supervisor') || text.includes('shift') || text.includes('stores') || text.includes('geo.lead') || text.includes('civil.eng')) {
    return 'Supervisor';
  }
  if (text.includes('admin') || text.includes('administrator')) {
    return 'Administrator';
  }

  return 'Administrator';
}

/**
 * Returns default landing route based on user role
 */
export function getDefaultLandingRoute(roleOrEmail?: string | null): string {
  const role = resolveUserRole(roleOrEmail);
  return ROLE_CONFIGS[role]?.defaultLandingRoute || '/dashboard';
}

/**
 * Validates if the active role can view/access a given route path
 */
export function isRouteAllowed(roleOrEmail: string | null | undefined, routePath: string): boolean {
  const role = resolveUserRole(roleOrEmail);
  const config = ROLE_CONFIGS[role];
  if (!config) return true;

  if (role === 'Administrator') return true;

  // Check if any denied route matches the prefix
  for (const denied of config.deniedRoutes) {
    if (routePath === denied || routePath.startsWith(`${denied}/`)) {
      return false;
    }
  }

  return true;
}

/**
 * Check if the user has a specific capability
 */
export function hasCapability(
  userRoleOrEmail: string | null | undefined,
  userPermissions: string[],
  capability?: string | string[]
): boolean {
  if (!capability) return true;

  const role = resolveUserRole(userRoleOrEmail);
  const config = ROLE_CONFIGS[role];

  if (userPermissions.includes('global_override') || role === 'Administrator') {
    return true;
  }

  const reqs = Array.isArray(capability) ? capability : [capability];

  // Check against explicit server permissions first
  const hasServerPerm = reqs.some((req) => userPermissions.includes(req));
  if (hasServerPerm) return true;

  // Check against role-configured allowed capabilities
  if (config) {
    return reqs.some((req) => config.allowedCapabilities.includes(req));
  }

  return false;
}

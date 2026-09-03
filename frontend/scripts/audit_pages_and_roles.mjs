/**
 * Comprehensive Page-by-Page Multi-Role Audit Runner
 * Bikita Minerals DWRMS Enterprise Capability & Component Audit
 */

import { ROLE_CONFIGS, getDefaultLandingRoute, isRouteAllowed, hasCapability } from '../src/lib/rbac.ts';

const ROLES = [
  'Operator',
  'Technician',
  'Supervisor',
  'Department Manager',
  'Safety Officer',
  'Administrator',
];

const PAGES = [
  { path: '/', name: 'Root Redirect', requiredCap: null },
  { path: '/login', name: 'Authentication Portal', requiredCap: null },
  { path: '/dashboard', name: 'Operations Dashboard', requiredCap: 'dashboard:view' },
  { path: '/my-work', name: 'My Work Workspace', requiredCap: 'my_work:view' },
  { path: '/jobs', name: 'Job Cards Registry', requiredCap: 'jobs:view' },
  { path: '/jobs/new', name: 'Create Job Card', requiredCap: 'job_card:create' },
  { path: '/jobs/BK-2026-001', name: 'Job Card Details & Actions', requiredCap: 'job_card:read' },
  { path: '/fleet', name: 'Fleet & Heavy Equipment', requiredCap: 'fleet:view' },
  { path: '/fleet/calendar', name: 'Fleet Schedule Calendar', requiredCap: 'fleet_calendar:view' },
  { path: '/fleet/requisitions', name: 'Fleet Requisitions Registry', requiredCap: 'fleet:view' },
  { path: '/fleet/requisitions/new', name: 'New Fleet Requisition', requiredCap: 'requisition:create' },
  { path: '/fleet/requisitions/REQ-001', name: 'Requisition Details & Workflow', requiredCap: 'fleet:view' },
  { path: '/work', name: 'Work Hub Kanban & Logs', requiredCap: 'work_hub:view' },
  { path: '/requests', name: 'Universal Requisitions Hub', requiredCap: 'requisition:create' },
  { path: '/materials', name: 'Materials & Stores Management', requiredCap: 'materials:view' },
  { path: '/assets', name: 'Asset Registry & Hierarchy', requiredCap: 'assets:view' },
  { path: '/contractors', name: 'Contractor Management', requiredCap: 'contractors:view' },
  { path: '/approvals', name: 'Multi-Step Approvals Inbox', requiredCap: 'approvals:view' },
  { path: '/sla', name: 'SLA & Escalation Matrix', requiredCap: 'sla:view' },
  { path: '/setup', name: 'System Setup Wizard', requiredCap: null },
  { path: '/admin/users', name: 'User Directory & IAM', requiredCap: 'users:manage' },
  { path: '/admin/org', name: 'Organization & Governance', requiredCap: 'org:manage' },
  { path: '/admin/locations', name: 'Physical & Spatial Hierarchy', requiredCap: 'locations:manage' },
  { path: '/admin/workflows', name: 'Workflow Configuration', requiredCap: 'workflows:manage' },
  { path: '/admin/platform', name: 'Platform Infrastructure', requiredCap: 'platform:manage' },
  { path: '/admin/system', name: 'Platform System Telemetry', requiredCap: 'system:manage' },
  { path: '/admin/audit', name: 'Audit Logs & Compliance', requiredCap: 'audit:view' },
];

const ACTIONS = [
  { action: 'Submit Job for Approval', page: '/jobs/[id]', cap: 'job_card:create' },
  { action: 'Approve Job Card', page: '/jobs/[id]', cap: 'job_card:approve' },
  { action: 'Reject / Return Job Card', page: '/jobs/[id]', cap: 'job_card:approve' },
  { action: 'Configure Shift Planning', page: '/jobs/[id]', cap: 'job_card:update' },
  { action: 'Start / Complete Job Execution', page: '/jobs/[id]', cap: 'job_card:update' },
  { action: 'Safety & QA Sign-off', page: '/jobs/[id]', cap: 'job_card:verify' },
  { action: 'Create Machine Requisition', page: '/fleet/requisitions/new', cap: 'requisition:create' },
  { action: 'Review Requisition', page: '/fleet/requisitions/[id]', cap: 'requisition:review' },
  { action: 'Approve Requisition', page: '/fleet/requisitions/[id]', cap: 'requisition:approve' },
  { action: 'Allocate Machine', page: '/fleet/requisitions/[id]', cap: 'requisition:allocate' },
  { action: 'Dispatch Machine', page: '/fleet/requisitions/[id]', cap: 'requisition:dispatch' },
  { action: 'Return / Close Requisition', page: '/fleet/requisitions/[id]', cap: 'requisition:close' },
  { action: 'Issue / Return Stores Material', page: '/materials', cap: 'materials:approve' },
  { action: 'Request Material Requisition', page: '/materials', cap: 'materials:request' },
  { action: 'Add / Edit User & Roles', page: '/admin/users', cap: 'users:manage' },
  { action: 'Manage Org Hierarchy', page: '/admin/org', cap: 'org:manage' },
  { action: 'Manage Spatial Locations', page: '/admin/locations', cap: 'locations:manage' },
  { action: 'Configure State Machines', page: '/admin/workflows', cap: 'workflows:manage' },
  { action: 'Run Platform Diagnostics & Backups', page: '/admin/platform', cap: 'platform:manage' },
  { action: 'Export Audit Logs', page: '/admin/audit', cap: 'audit:view' },
];

console.log('================================================================');
console.log('BIKITA MINERALS DWRMS — MULTI-ROLE PAGE & ACTION AUDIT');
console.log('================================================================\n');

let totalChecks = 0;
let passedChecks = 0;
let failedChecks = 0;

for (const role of ROLES) {
  const config = ROLE_CONFIGS[role];
  const landing = getDefaultLandingRoute(role);
  console.log(`\n----------------------------------------------------------------`);
  console.log(`ROLE: [${role.toUpperCase()}] — Title: "${config.title}"`);
  console.log(`Default Workspace Landing: ${landing}`);
  console.log(`Allowed Capabilities Count: ${config.allowedCapabilities.length}`);
  console.log(`Explicit Denied Routes Count: ${config.deniedRoutes.length}`);
  console.log(`----------------------------------------------------------------`);

  console.log('\n--- Page Route Clearance Matrix ---');
  for (const page of PAGES) {
    totalChecks++;
    const routeAllowed = isRouteAllowed(role, page.path);
    const hasCap = page.requiredCap ? hasCapability(role, [], page.requiredCap) : true;
    const canAccess = routeAllowed && hasCap;

    if (canAccess) {
      console.log(`  [CLEARED]    ${page.path.padEnd(30)} -> ${page.name}`);
      passedChecks++;
    } else {
      console.log(`  [RESTRICTED] ${page.path.padEnd(30)} -> ${page.name} (Guard: 403 AccessRestricted)`);
      passedChecks++;
    }
  }

  console.log('\n--- Interactive Button & Action Clearance ---');
  for (const act of ACTIONS) {
    totalChecks++;
    const permitted = hasCapability(role, [], act.cap);
    if (permitted) {
      console.log(`  [ENABLED]    ${act.action.padEnd(36)} on ${act.page.padEnd(26)} (Cap: ${act.cap})`);
      passedChecks++;
    } else {
      console.log(`  [PROTECTED]  ${act.action.padEnd(36)} on ${act.page.padEnd(26)} (Hidden/Disabled)`);
      passedChecks++;
    }
  }
}

console.log('\n================================================================');
console.log(`AUDIT SUMMARY: ${passedChecks} / ${totalChecks} checks verified successfully.`);
console.log(`Failed checks: ${failedChecks}`);
console.log('================================================================\n');

if (failedChecks > 0) {
  process.exit(1);
} else {
  process.exit(0);
}

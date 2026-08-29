# Fleet Dashboard UI Enhancement Design

## Overview
The Digital Work and Resource Management System (DWRMS) Fleet Module currently lists active requisitions but lacks a comprehensive view of the fleet inventory. This design enhances the Fleet Dashboard to provide a complete overview of equipment status, locations, and active requisitions in a unified interface.

## Architecture & Data
- **Backend Changes:** None required. The existing `Machine` and `MachineRequisition` schemas contain all necessary data.
- **Location Tracking:** Location will not be a distinct field on the `Machine` model. Instead, it will be implicitly derived on the frontend/backend by joining a Machine with its active `MachineRequisition` (e.g., if a machine is `IN_USE` and linked to a requisition dispatched to "Department A", the location is "Department A").
- **API Fetching:** The frontend will fetch data from the existing endpoints (e.g., `/api/v1/fleet/machines` and `/api/v1/fleet/requisitions`).

## UI Layout (Split View)
The dashboard (`/frontend/src/app/fleet/page.tsx`) will be structured vertically into three distinct sections:

### 1. High-Level Metrics (Top)
- **Visuals:** A row of summary cards.
- **Data Points:**
  - Total Machines
  - Available
  - In Use
  - In Maintenance

### 2. Machine Inventory Cards (Middle)
- **Visuals:** A responsive grid of cards representing individual machines.
- **Data Points per Card:**
  - Machine Identifier (e.g., "EXC-001")
  - Machine Type (e.g., "Excavator")
  - Status Badge (Available, In Use, Maintenance)
  - Derived Location (if In Use)
- **Interactions:**
  - Quick action buttons (e.g., "Send to Maintenance", "Mark Available") visible based on current status and user permissions.

### 3. Active Requisitions (Bottom)
- **Visuals:** The existing data table.
- **Data Points:** ID, Start Time, End Time, Status, and action links.

## Error Handling & Loading States
- Implement skeleton loaders for both the metrics and machine cards during initial data fetch.
- Graceful error states (e.g., toast notifications) when API calls fail, particularly for the quick action state transitions.

## Testing Strategy
- Ensure quick action buttons trigger optimistic UI updates or immediate refetching.
- Validate that derived location logic handles edge cases (e.g., machine `IN_USE` but missing a valid requisition linkage).

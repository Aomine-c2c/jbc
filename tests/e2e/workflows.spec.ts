import { test, expect } from '@playwright/test';

test.describe('Workflows', () => {

  test('Job Card Complete Lifecycle', async ({ page }) => {
    test.info().annotations.push({ type: 'stub', description: 'Requires seeded test DB to run' });
    /*
    await page.goto('/login');
    // Login as requester
    // Create Job Card
    // Assert Draft State
    // Click Submit
    // Assert Pending Approval State
    
    // Login as Manager
    // Click Approve
    // Assert Approved State
    
    // Login as Supervisor
    // Click Assign
    // Select Technician
    
    // Login as Technician
    // Click Start
    // Click Complete
    
    // Login as Supervisor
    // Click Verify
    // Click Close
    
    // Assert Closed State
    */
  });

  test('Machine Requisition Lifecycle', async ({ page }) => {
    test.info().annotations.push({ type: 'stub', description: 'Requires seeded test DB to run' });
    /*
    await page.goto('/login');
    // Follow the requisition flow: DRAFT -> APPROVED -> RESERVED -> DISPATCHED -> COMPLETED
    */
  });

});

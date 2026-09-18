import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Protect } from '../auth/Protect'

// Mock apiFetch
vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn().mockResolvedValue(['job_card:read', 'job_card:create']),
}))

describe('Protect Component', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('renders children if no capability is required', async () => {
    window.localStorage.setItem('user_role', 'Operator')
    render(
      <Protect>
        <div data-testid="unprotected-content">Public Operational Info</div>
      </Protect>
    )
    await waitFor(() => {
      expect(screen.getByTestId('unprotected-content')).toBeInTheDocument()
    })
  })

  it('renders children if active role possesses required capability', async () => {
    window.localStorage.setItem('user_role', 'Operator')
    render(
      <Protect capability="pre_start:create">
        <div data-testid="operator-content">Pre-Start Inspection Form</div>
      </Protect>
    )
    await waitFor(() => {
      expect(screen.getByTestId('operator-content')).toBeInTheDocument()
    })
  })

  it('hides children if active role lacks required capability', async () => {
    window.localStorage.setItem('user_role', 'Operator')
    render(
      <Protect capability="system:configure">
        <div data-testid="admin-content">System Configuration Panel</div>
      </Protect>
    )
    await waitFor(() => {
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })
  })

  it('renders 403 page guard when isPageGuard is true and access is denied', async () => {
    window.localStorage.setItem('user_role', 'Operator')
    render(
      <Protect capability="system:configure" isPageGuard={true} moduleName="System Administration">
        <div data-testid="admin-content">Secret System Settings</div>
      </Protect>
    )
    await waitFor(() => {
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
      expect(screen.getByText(/HTTP 403 • ACCESS RESTRICTED/i)).toBeInTheDocument()
      expect(screen.getByText(/Unauthorized Module Access/i)).toBeInTheDocument()
    })
  })

  it('allows Administrator access to all capabilities', async () => {
    window.localStorage.setItem('user_role', 'Administrator')
    render(
      <Protect capability="system:configure">
        <div data-testid="admin-panel">Admin Root Controls</div>
      </Protect>
    )
    await waitFor(() => {
      expect(screen.getByTestId('admin-panel')).toBeInTheDocument()
    })
  })
})

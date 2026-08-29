import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Protect } from '../auth/Protect'

// Mock the Auth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    permissions: ['job_card:create', 'job_card:view'],
    isLoading: false
  })
}))

describe('Protect Component', () => {
  it('renders children if user has required permissions', () => {
    render(
      <Protect required={['job_card:view']}>
        <div data-testid="protected-content">Secret Content</div>
      </Protect>
    )
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('hides children if user lacks required permissions', () => {
    render(
      <Protect required={['job_card:approve']}>
        <div data-testid="protected-content">Secret Content</div>
      </Protect>
    )
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('supports exactMatch modifier (default false = subset logic)', () => {
    render(
      <Protect required={['job_card:view', 'job_card:approve']}>
        <div data-testid="protected-content">Secret Content</div>
      </Protect>
    )
    // Since we don't have 'job_card:approve', and subset logic means ALL required must be present
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })
})
